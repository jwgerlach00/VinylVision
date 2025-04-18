import sys

from discogs_client.exceptions import HTTPError
from discogs.utils import update_qs


class SimpleFieldDescriptor(object):
    """
    An attribute that determines its value using the object's fetch() method.

    If transform is a callable, the value will be passed through transform when
    read. Useful for strings that should be ints, parsing timestamps, etc.

    Shorthand for:

        @property
        def foo(self):
            return self.fetch('foo')
    """
    def __init__(self, name, writable=False, transform=None):
        self.name = name
        self.writable = writable
        self.transform = transform

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.fetch(self.name)
        if self.transform:
            value = self.transform(value)
        return value

    def __set__(self, instance, value):
        if self.writable:
            instance.changes[self.name] = value
            return
        raise AttributeError("can't set attribute")


class ObjectFieldDescriptor(object):
    """
    An attribute that determines its value using the object's fetch() method,
    and passes the resulting value through an APIObject.

    If optional = True, the value will be None (rather than an APIObject
    instance) if the key is missing from the response.

    If as_id = True, the value is treated as an ID for the new APIObject rather
    than a partial dict of the APIObject.

    Shorthand for:

        @property
        def baz(self):
            return BazClass(self.client, self.fetch('baz'))
    """
    def __init__(self, name, class_name, optional=False, as_id=False):
        self.name = name
        self.class_name = class_name
        self.optional = optional
        self.as_id = as_id

    def __get__(self, instance, owner):
        if instance is None:
            return self
        wrapper_class = CLASS_MAP[self.class_name.lower()]
        response_dict = instance.fetch(self.name)
        if self.optional and not response_dict:
            return None
        if self.as_id:
            # Response_dict wasn't really a dict. Make it so.
            response_dict = {'id': response_dict}
        return wrapper_class(instance.client, response_dict)

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


class ListFieldDescriptor(object):
    """
    An attribute that determines its value using the object's fetch() method,
    and passes each item in the resulting list through an APIObject.

    Shorthand for:

        @property
        def bar(self):
            return [BarClass(self.client, d) for d in self.fetch('bar', [])]
    """
    def __init__(self, name, class_name):
        self.name = name
        self.class_name = class_name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        wrapper_class = CLASS_MAP[self.class_name.lower()]
        return [wrapper_class(instance.client, d) for d in instance.fetch(self.name, [])]

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


class ObjectCollectionDescriptor(object):
    """
    An attribute that determines its value by fetching a URL to a paginated
    list of related objects, and passes each item in the resulting list through
    an APIObject.

    Shorthand for:

        @property
        def frozzes(self):
            return PaginatedList(self.client, self.fetch('frozzes_url'), 'frozzes', FrozClass)
    """
    def __init__(self, name, class_name, url_key=None, list_class=None):
        self.name = name
        self.class_name = class_name

        if url_key is None:
            url_key = name + '_url'
        self.url_key = url_key

        if list_class is None:
            list_class = PaginatedList
        self.list_class = list_class

    def __get__(self, instance, owner):
        if instance is None:
            return self
        wrapper_class = CLASS_MAP[self.class_name.lower()]
        return self.list_class(instance.client, instance.fetch(self.url_key), self.name, wrapper_class)

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


class Field(object):
    """
    A placeholder for a descriptor. Is transformed into a descriptor by the
    APIObjectMeta metaclass when the APIObject classes are created.
    """
    _descriptor_class = None

    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop('key', None)
        self.args = args
        self.kwargs = kwargs

    def to_descriptor(self, attr_name):
        return self._descriptor_class(self.key or attr_name, *self.args, **self.kwargs)


class SimpleField(Field):
    """A field that just returns the value of a given JSON key."""
    _descriptor_class = SimpleFieldDescriptor


class ListField(Field):
    """A field that returns a list of APIObjects."""
    _descriptor_class = ListFieldDescriptor


class ObjectField(Field):
    """A field that returns a single APIObject."""
    _descriptor_class = ObjectFieldDescriptor


class ObjectCollection(Field):
    """A field that returns a paginated list of APIObjects."""
    _descriptor_class = ObjectCollectionDescriptor


class APIObjectMeta(type):
    def __new__(cls, name, bases, dict_):
        for k, v in dict_.items():
            if isinstance(v, Field):
                dict_[k] = v.to_descriptor(k)
        return super(APIObjectMeta, cls).__new__(cls, name, bases, dict_)


class APIObject(metaclass=APIObjectMeta):
    def repr_str(self, string):
        if sys.version_info < (3,):
            return string.encode('utf-8')
        return string


class PrimaryAPIObject(APIObject):
    """A first-order API object that has a canonical endpoint of its own."""
    def __init__(self, client, dict_):
        self.data = dict_
        self.client = client
        self._known_invalid_keys = []
        self.changes = {}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        return NotImplemented if equal is NotImplemented else not equal

    def refresh(self):
        if self.data.get('resource_url'):
            data = self.client._get(self.data['resource_url'])
            self.data.update(data)
            self.changes = {}

    def save(self):
        if self.data.get('resource_url'):
            # TODO: This should be PATCH
            self.client._post(self.data['resource_url'], self.changes)

            # Refresh the object, in case there were side-effects
            self.refresh()

    def delete(self):
        if self.data.get('resource_url'):
            self.client._delete(self.data['resource_url'])

    def fetch(self, key, default=None):
        if key in self._known_invalid_keys:
            return default

        try:
            # First, look in the cache of pending changes
            return self.changes[key]
        except KeyError:
            pass

        try:
            # Next, look in the potentially incomplete local cache
            return self.data[key]
        except KeyError:
            pass

        # Now refresh the object from its resource_url.
        # The key might exist but not be in our cache.
        self.refresh()

        try:
            return self.data[key]
        except:
            self._known_invalid_keys.append(key)
            return default


# This is terribly cheesy, but makes the client API more consistent
class SecondaryAPIObject(APIObject):
    """
    An object that wraps parts of a response and doesn't have its own
    endpoint.
    """
    def __init__(self, client, dict_):
        self.client = client
        self.data = dict_

    def fetch(self, key, default=None):
        return self.data.get(key, default)


class BasePaginatedResponse(object):
    """Base class for lists of objects spread across many URLs."""
    def __init__(self, client, url):
        self.client = client
        self.url = url
        self._num_pages = None
        self._num_items = None
        self._pages = {}
        self._per_page = 50
        self._list_key = 'items'
        self._sort_key = None
        self._sort_order = 'asc'
        self._filters = {}

    @property
    def per_page(self):
        return self._per_page

    @per_page.setter
    def per_page(self, value):
        self._per_page = value
        self._invalidate()

    def _invalidate(self):
        self._pages = {}
        self._num_pages = None
        self._num_items = None

    def _load_pagination_info(self):
        data = self.client._get(self._url_for_page(1))
        self._pages[1] = [
            self._transform(item) for item in data[self._list_key]
        ]
        self._num_pages = data['pagination']['pages']
        self._num_items = data['pagination']['items']

    def _url_for_page(self, page):
        base_qs = {
            'page': page,
            'per_page': self._per_page,
        }

        if self._sort_key is not None:
            base_qs.update({
                'sort': self._sort_key,
                'sort_order': self._sort_order,
            })

        base_qs.update(self._filters)

        return update_qs(self.url, base_qs)

    def sort(self, key, order='asc'):
        if order not in ('asc', 'desc'):
            raise ValueError("Order must be one of 'asc', 'desc'")
        self._sort_key = key
        self._sort_order = order
        self._invalidate()
        return self

    def filter(self, **kwargs):
        self._filters = kwargs
        self._invalidate()
        return self

    @property
    def pages(self):
        if self._num_pages is None:
            self._load_pagination_info()
        return self._num_pages

    @property
    def count(self):
        if self._num_items is None:
            self._load_pagination_info()
        return self._num_items

    def page(self, index):
        if index not in self._pages:
            data = self.client._get(self._url_for_page(index))
            self._pages[index] = [
                self._transform(item) for item in data[self._list_key]
            ]
        return self._pages[index]

    def _transform(self, item):
        return item

    def __getitem__(self, index):
        page_index = index // self.per_page + 1
        offset = index % self.per_page

        try:
            page = self.page(page_index)
        except HTTPError as e:
            if e.status_code == 404:
                raise IndexError(e.msg)
            else:
                raise

        return page[offset]

    def __len__(self):
        return self.count

    def __iter__(self):
        for i in range(1, self.pages + 1):
            page = self.page(i)
            for item in page:
                yield item


class PaginatedList(BasePaginatedResponse):
    """A paginated list of objects of a particular class."""
    def __init__(self, client, url, key, class_):
        super(PaginatedList, self).__init__(client, url)
        self._list_key = key
        self.class_ = class_

    def _transform(self, item):
        return self.class_(self.client, item)


class MixedPaginatedList(BasePaginatedResponse):
    """A paginated list of objects identified by their type parameter."""
    def __init__(self, client, url, key):
        super(MixedPaginatedList, self).__init__(client, url)
        self._list_key = key

    def _transform(self, item):
        # In some cases, we want to map the 'title' key we get back in search
        # results to 'name'. This way, you can repr() a page of search results
        # without making 50 requests.
        if item['type'] in ('label', 'artist'):
            item['name'] = item['title']

        return CLASS_MAP[item['type']](self.client, item)


class Artist(PrimaryAPIObject):
    id = SimpleField()
    name = SimpleField()
    real_name = SimpleField(key='realname')
    images = SimpleField()
    profile = SimpleField()
    data_quality = SimpleField()
    name_variations = SimpleField(key='namevariations')
    url = SimpleField(key='uri')
    urls = SimpleField()
    aliases = ListField('Artist')
    members = ListField('Artist')
    groups = ListField('Artist')

    def __init__(self, client, dict_):
        super(Artist, self).__init__(client, dict_)
        self.data['resource_url'] = '{0}/artists/{1}'.format(client._base_url, dict_['id'])

    @property
    def releases(self):
        return MixedPaginatedList(self.client, self.fetch('releases_url'), 'releases')

    def __repr__(self):
        return self.repr_str('<Artist {0!r} {1!r}>'.format(self.id, self.name))


class Release(PrimaryAPIObject):
    id = SimpleField()
    title = SimpleField()
    year = SimpleField()
    thumb = SimpleField()
    data_quality = SimpleField()
    status = SimpleField()
    genres = SimpleField()
    images = SimpleField()
    country = SimpleField()
    notes = SimpleField()
    formats = SimpleField()
    styles = SimpleField()
    url = SimpleField(key='uri')
    # videos = ListField('Video')
    tracklist = ListField('Track')
    artists = ListField('Artist')
    credits = ListField('Artist', key='extraartists')
    labels = ListField('Label')
    companies = ListField('Label')

    def __init__(self, client, dict_):
        super(Release, self).__init__(client, dict_)
        self.data['resource_url'] = '{0}/releases/{1}'.format(client._base_url, dict_['id'])

    @property
    def master(self):
        master_id = self.fetch('master_id')
        if master_id:
            return Master(self.client, {'id': master_id})
        else:
            return None

    def __repr__(self):
        return self.repr_str('<Release {0!r} {1!r}>'.format(self.id, self.title))


class Master(PrimaryAPIObject):
    id = SimpleField()
    title = SimpleField()
    data_quality = SimpleField()
    styles = SimpleField()
    genres = SimpleField()
    images = SimpleField()
    url = SimpleField(key='uri')
    videos = ListField('Video')
    tracklist = ListField('Track')
    main_release = ObjectField('Release', as_id=True)
    versions = ObjectCollection('Release')

    def __init__(self, client, dict_):
        super(Master, self).__init__(client, dict_)
        self.data['resource_url'] = '{0}/masters/{1}'.format(client._base_url, dict_['id'])

    def __repr__(self):
        return self.repr_str('<Master {0!r} {1!r}>'.format(self.id, self.title))


class Label(PrimaryAPIObject):
    id = SimpleField()
    name = SimpleField()
    profile = SimpleField()
    urls = SimpleField()
    images = SimpleField()
    contact_info = SimpleField()
    data_quality = SimpleField()
    url = SimpleField(key='uri')
    sublabels = ListField('Label')
    parent_label = ObjectField('Label', optional=True)
    releases = ObjectCollection('Release')

    def __init__(self, client, dict_):
        super(Label, self).__init__(client, dict_)
        self.data['resource_url'] = '{0}/labels/{1}'.format(client._base_url, dict_['id'])

    def __repr__(self):
        return self.repr_str('<Label {0!r} {1!r}>'.format(self.id, self.name))


class Track(SecondaryAPIObject):
    duration = SimpleField()
    position = SimpleField()
    title = SimpleField()
    artists = ListField('Artist')
    credits = ListField('Artist', key='extraartists')

    def __repr__(self):
        return self.repr_str('<Track {0!r} {1!r}>'.format(self.position, self.title))
    
    def get_side(self):
        if self.position:
            # Assuming position is in the format "A1", "B2", etc.
            return self.position[0]
        return None
    
    def get_track_number(self):
        if self.position:
            # Assuming position is in the format "A1", "B2", etc.
            return int(self.position[1:])
        return None


CLASS_MAP = {
    'artist': Artist,
    'release': Release,
    'master': Master,
    'label': Label,
    'track': Track
}
