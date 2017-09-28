from __future__ import absolute_import

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from numpy.testing import assert_equal
import quantities as pq
from neo.io.blackrockio import BlackrockIO
from neo.io.blackrockio_v4 import BlackrockIO as old_brio
import warnings
import numpy as np
from neo.core import *
from neo import AnalogSignal
import time
from itertools import izip_longest

# check scipy
try:
    from distutils import version
    import scipy.io
    import scipy.version
except ImportError as err:
    HAVE_SCIPY = False
    SCIPY_ERR = err
# dummy class used only for automatic downloading of test data
#  class DownloadDataIO(BaseTestIO, unittest.TestCase):
#      ioclass = BlackrockIO
#      files_to_download = [
#          'FileSpec2.3001.nev',
#          'FileSpec2.3001.ns5',
#          'FileSpec2.3001.ccf',
#          'FileSpec2.3001.mat']

dirname = '/home/arbeit/Downloads/files_for_testing_neo/blackrock/FileSpec2.3001'
oldbrio_reader = None
newbrio_reader = None


def old_brio_load():
    # ioclass = old_brio
    # files_to_test = ['FileSpec2.3001']
    oldbrio_reader = old_brio(dirname)
    old_block = oldbrio_reader.read_block(
        # n_starts=[None], n_stops=None,
        channels={1, 2, 3, 4, 5, 6, 7, 8, 129, 130},
        nsx_to_load=5,
        units='all',
        load_events=True,
        load_waveforms=True)
    # output(old_block)
    print 'Loading old IO done'
    return old_block


def new_brio_load():
    newbrio_reader = BlackrockIO(dirname)
    # new_block = newbrio_reader.read_block()
    new_block = newbrio_reader.read_block(load_waveforms=True)
    # output(new_block)
    print 'Loading new IO done'
    return new_block


class outputComparison():
    # old_block = None
    # new_block = None

    def __init__(self):  # , old_block, new_block):
        # print(old_block, new_block)
        # self.old_block = old_block
        # self.new_block = new_block
        print('Loading  comparison')

    @staticmethod
    def compare(block1, block2):
        object_types_to_test = ['Segment', 'ChannelIndex', 'Unit', 'AnalogSignal',
                                'SpikeTrain', 'Event', 'Epoch']
        print('*'*30, 'Testing {}'.format('Block'))
        compare_objects(block1, block2, 'Block')
        for objtype in object_types_to_test:
            print('*'*30, 'Testing {}'.format(objtype))
            objects1 = block1.list_children_by_class(objtype)
            objects2 = block2.list_children_by_class(objtype)
            if len(objects1) != len(objects2):
                print('Number of ', objtype, ' is different in the blocks: ', len(objects1), ' != ', len(objects2))
            # index = 0
            # Loop through Objects and compare them, even if not same number, to find which objects are the same
            for obj1, obj2 in izip_longest(objects1, objects2, fillvalue=None):
                # index += 1
                if obj1 is not None and obj2 is not None:
                    compare_objects(obj1, obj2, objtype)
                elif obj1 is None:
                    print('Additional object in 2. (new) version: ', obj2.name)
                elif obj2 is None:
                    print('Additional object in 1. (old) version: ', obj1.name)


def compare_objects(obj1, obj2, objtype):
    compare_annotations(obj1.annotations, obj2.annotations)
    compare_attributes(obj1, obj2)
    if objtype in ['Event', 'AnalogSignal', 'SpikeTrain']:
        compare_arrays(obj1, obj2, objtype)
    compare_links(obj1, obj2, objtype)


def compare_annotations(annos1, annos2):
    if len(annos1) != len(annos2) or annos1.keys != annos2.keys:
        print('Annotations are not the same! Keys ', annos1.keys(), ' != ', annos2.keys())
        common_keys = []
        uncommon_keys1 = []
        uncommon_keys2 = []
        for key in annos1.keys():   # Save common keys in list, print if not in common
            if key in annos2.keys():
                common_keys.append(key)
            else:
                print('This key from the 1. (old) version does not exist in 2. (new) version: ', key)
                uncommon_keys1.append(key)
        for key in annos2.keys():
            if key not in common_keys:
                print('This key from the 2. (new) version does not exist in 1. (old) version: ', key)
                uncommon_keys2.append(key)

        for key in common_keys:  # Compare values for common keys
            if annos1[key] != annos2[key]:
                print('Values of annotations differ for key', key, ': ', annos1[key], ' != ', annos2[key])
        # Loop through not common keys and try to find corresponding value anywhere in other version
        for key1 in uncommon_keys1:
            for key2 in annos2.keys():
                if annos1[key1] == annos2[key2]:
                    print('Value of ', key1, ' in 1. (old) version can be found in 2. (new) version with key ', key2)
        for key2 in uncommon_keys2:
            for key1 in annos1.keys():
                if annos1[key1] == annos2[key2]:
                    print('Value of ', key2, ' in 2. (new) version can be found in 1. (old) version with key ', key1)
    else:
        if annos1.keys() == annos2.keys():
            difference_found = False
            for key in annos1.keys():
                if annos1[key] != annos2[key]:
                    print('Values of annotations differ for key', key, ': ', annos1[key], ' != ', annos2[key])
                    difference_found = True
            if not difference_found:
                print('Annotations are the same')
    print('*'*10)


def compare_attributes(obj1, obj2):     # Is this enough? Or can values of attribute be in attribute with different name?
    possible_attrs = obj1._all_attrs
    assert possible_attrs == obj2._all_attrs
    difference_found = False
    for attr in possible_attrs:
        if attr[0] in ['signal', 'times', 'waveforms', 'labels']:
            print('Arrays are skipped here')
        elif not obj1.__getattribute__(attr[0]) == obj2.__getattribute__(attr[0]):
            difference_found = True
            print('Attribute values of ', attr, 'are not the same: ',
                  obj1.__getattribute__(attr[0]), ' != ', obj2.__getattribute__(attr[0]))
    if not difference_found:
        print('Attributes are the same')


def compare_arrays(obj1, obj2, objtype):
    rescale_factor = 1
    difference_found = False
    arr1 = []
    arr2 = []
    if objtype == 'AnalogSignal':
        arr1 = obj1[:].magnitude
        arr2 = obj2[:].magnitude
        if obj1.units != obj2.units:
            print('Units of these ', objtype, ' arrays differ: ', obj1.units, ' != ', obj2.units)
        rescale_factor = arr2[0]/arr1[0]
        difference_found = compare_arr(arr1, arr2, rescale_factor)
    elif objtype == 'SpikeTrain':
        arr1 = obj1.times[:].magnitude
        arr2 = obj2.times[:].magnitude
        if obj1.units != obj2.units:
            print('Units of these ', objtype, ' arrays differ: ', obj1.units, ' != ', obj2.units)
        rescale_factor = arr2[0]/arr1[0]
        difference_found = compare_arr(arr1, arr2, rescale_factor)
        arr1 = obj1.waveforms[:].magnitude
        arr2 = obj2.waveforms[:].magnitude
        if obj1.units != obj2.units:
            print('Units of these ', objtype, ' arrays differ: ', obj1.units, ' != ', obj2.units)
        rescale_factor = arr2[0]/arr1[0]
        if compare_arr(arr1, arr2, rescale_factor):
            difference_found = False
    elif objtype == 'Event':
        arr1 = obj1.times[:].magnitude
        arr2 = obj2.times[:].magnitude
        if obj1.units != obj2.units:
            print('Units of these ', objtype, ' arrays differ: ', obj1.units, ' != ', obj2.units)
        rescale_factor = arr2/arr1[0]
        difference_found = compare_arr(arr1, arr2, rescale_factor)
        arr1 = obj1.labels[:]
        arr2 = obj2.labels[:]
        rescale_factor = 1
        if compare_arr(arr1, arr2, rescale_factor):
            difference_found = False
    if not difference_found:
        rescale_factor_used = rescale_factor
        if isinstance(rescale_factor, np.ndarray) and len(rescale_factor) > 1:
            rescale_factor_used = rescale_factor[0]
        print('Array values are similar. Values in array of 2. (new) version are ', rescale_factor_used,
              ' times as high as in 1. (old) version')


def compare_arr(array1, array2, rescale_factor):    # Implement percentages of equality
    if not isinstance(rescale_factor, np.ndarray) and rescale_factor != 1:
        array2 /= rescale_factor
    elif isinstance(rescale_factor, np.ndarray) and len(rescale_factor > 0):
        array2 /= rescale_factor[0]
    # difference_found = False
    if len(array1) != len(array2):
        print('Different length of Arrays!!')
        return True
    else:
        print('Length is the same, testing for equality: ')
        if (array1 != array2).any():
            return False
        # for a, b in zip(array1, array2):
        #     if (a != b).any():
        #         difference_found = True
        # if difference_found:
        #     print('Values are not the same even after rescaling')
        # return difference_found


def compare_links(obj1, obj2, objtype):
    objtype = str(objtype)
    all_links1 = []
    all_links2 = []
    links_to_check = dict(Block=['channel_indexes', 'segments'], ChannelIndex=['analogsignals', 'units', 'block'],
                          Unit=['spiketrains', 'channel_index'], AnalogSignal=['channel_index', 'segment'],
                          SpikeTrain=['unit', 'segment'],
                          Segment=['block', 'events', 'epochs', 'spiketrains', 'analogsignals'],
                          Event=['segment'], Epoch=['segment'])
    for link in links_to_check[objtype]:
        if isinstance(obj1.__getattribute__(link), np.ndarray) or isinstance(obj2.__getattribute__(link), list):
            for a in obj1.__getattribute__(link):
                all_links1.append(link)
        elif obj1.__getattribute__(link) is not None:
            all_links1.append(link)
    for link in links_to_check[objtype]:
        if isinstance(obj2.__getattribute__(link), np.ndarray) or isinstance(obj2.__getattribute__(link), list):
            for a in obj2.__getattribute__(link):
                all_links2.append(link)
        elif obj2.__getattribute__(link) is not None:
            all_links2.append(link)
    # Actual comparison comes here
    if all_links1 == all_links2:
        print('Links of this ', objtype, 'object are the same as before')
        # Does not cover the case that objects have changed, eg. St is linked to Unit1 instead of Unit2
        return
    else:
        if len(all_links1)!=len(all_links2):
            print('Different number of links to other objects for this ', objtype)
        a = 0
        b = 0
        while a<len(all_links1) and b < len(all_links2):
            if all_links1[a] == all_links2[b]:
                a += 1
                b += 1
                continue
            else:
                if links_to_check[objtype].index(all_links1[a]) < links_to_check[objtype].index(all_links2[b]):
                    print('2. (new) version does not have as many links to ', link, 's as 1. (old) version')
                    a += 1
                else:
                    print('2. (new) version has more links to ', objtype, 's than 1. (old) version')
                    b += 1
            if a == len(all_links1) and b < len(all_links2):
                a -= 1
            elif b == len(all_links2) and a < len(all_links1):
                b -= 1


outputComparison.compare(old_brio_load(), new_brio_load())
