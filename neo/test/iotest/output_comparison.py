from __future__ import absolute_import

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from numpy.testing import assert_equal
import numpy as np
import quantities as pq
from neo.io.blackrockio import BlackrockIO
from neo.io.blackrockio_v4 import BlackrockIO as old_brio
import warnings
import numpy as np
import quantities as pq
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
        for objtype in object_types_to_test:
            print('Testing {}'.format(objtype))
            objects1 = block1.list_children_by_class(objtype)
            objects2 = block2.list_children_by_class(objtype)
            if len(objects1) != len(objects2):
                print('Number of ', objtype, ' is different in the blocks: ', len(objects1), ' != ', len(objects2))
            # index = 0
            # Loop through Objects and compare them, even if not same number, to find which objects are the same
            for obj1, obj2 in izip_longest(objects1, objects2, fillvalue=None):
                # index += 1
                if obj1 is not None and obj2 is not None:
                    compare_annotations(obj1.annotations, obj2.annotations)
                    compare_attributes(obj1, obj2)
                    if objtype in [Event, AnalogSignal, SpikeTrain]:
                        compare_arrays(obj1, obj2, objtype)
                    compare_links(obj1, obj2, objtype)
                elif obj1 is None:
                    print('Additional object in 2. (new) version: ', obj2.name)
                elif obj2 is None:
                    print('Additional object in 1. (old) version: ', obj1.name)


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
    if objtype == AnalogSignal:
        arr1 = obj1[:].magnitude
        arr2 = obj2[:].magnitude
        rescale_factor = arr2[0]/arr1[0]
        difference_found = compare_arr(arr1, arr2, rescale_factor)
    elif objtype == SpikeTrain:
        arr1 = obj1.times[:].magnitude
        arr2 = obj2.times[:].magnitude
        rescale_factor = arr2[0]/arr1[0]
        difference_found = compare_arr(arr1, arr2, rescale_factor)
        arr1 = obj1.waveforms[:].magnitude
        arr2 = obj2.waveforms[:].magnitude
        rescale_factor = arr2[0]/arr1[0]
        if compare_arr(arr1, arr2, rescale_factor):
            difference_found = False
    elif objtype == Event:
        arr1 = obj1.times[:].magnitude
        arr2 = obj2.times[:].magnitude
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



# def output(block):
#     for seg in block.segments:
#         print('seg', seg.index)
#         for epoch in seg.epochs:
#             print("FOUND EPOCH")
#         for anasig in seg.analogsignals:
#             print(' AnalogSignal', anasig.name, anasig.shape, anasig.t_start, anasig.sampling_rate)
#             print('ChannelIndex', anasig.annotations['channel_id'])
#             # print(anasig.channel_index.channel_id) => SHOULD WORK; BUT DOESN'T!!!!!!!!!!!
#         for st in seg.spiketrains:
#             if st is not None:
#                 print(' SpikeTrain', st.name, st.shape, st.waveforms.shape, st.rescale(pq.s)[:5])
#         for ev in seg.events:
#             print(' Event', ev.name, ev.times.shape)
#     print ('*' * 10)
#
#
# # def count_channels(block):
# #     num_channels = 0
# #     for seg in block.segments:
# #         for anasig in seg.analogsignals:
# #             a = block.annotations
#
# def compare_neo_content(bl1, bl2):
#     print('*' * 5, 'Comparison of blocks', '*' * 5)
#     object_types_to_test = [Segment, ChannelIndex, Unit, AnalogSignal,
#                             SpikeTrain, Event, Epoch]
#     # object_types_to_test = [SpikeTrain]
#     for objtype in object_types_to_test:
#         print('Testing {}'.format(objtype))
#         children1 = bl1.list_children_by_class(objtype)
#         children2 = bl2.list_children_by_class(objtype)
#
#         if len(children1) != len(children2):
#             warnings.warn('Number of {} is different in both blocks ({} != {'
#                           '}). Skipping comparison'.format(objtype,
#                                                            len(children1),
#                                                            len(children2)))
#             continue
#
#         for child1, child2 in zip(children1, children2):
#             compare_annotations(child1.annotations, child2.annotations, objtype)
#             # compare_attributes(child1, child2)
#
#
# def compare_failing_classes(old_block,
#                             new_block):  # more precise comparison of the classes that fail compare_neo_content, here AnaSig, Event and ChannelIndex
#     print('*')
#
#
# def compare_annotations(anno1, anno2, objecttype):
#     if len(anno1) != len(anno2):
#         warnings.warn('Different numbers of annotations! {} != {'
#                       '}\nSkipping further comparison of this '
#                       'annotation list.'.format(
#             anno1.keys(), anno2.keys()))
#         print('In:', objecttype)
#         time.sleep(5)
#         return
#     assert anno1.keys() == anno2.keys()
#     for key in anno1.keys():
#         anno1[key] = anno2[key]
#
#
# def print_annotations_id(block,
#                          objtype):  # because comparison will always say false, so need to check content => for IDs
#     children1 = block.list_children_by_class(objtype)
#     for child1 in children1:
#         try:  # => if 'Unit_id' in child1.annotations   [.keys] => raus!!!
#             print('Unit_ID:', child1.annotations['unit_id'])
#         except:
#             pass
#         try:
#             print('Channel_ID:', child1.annotations['channel_id'])
#         except:
#             pass
#         try:
#             print('ID:', child1.annotations['id'])
#         except:
#             pass
#     print('*' * 10)
#
#
# def print_annotations_all(
#         block,
#         objtype):
#     objects = block.list_children_by_class(objtype)
#     print ('Object Type: ', objtype)
#     for obj in objects:
#         for key in obj.annotations.keys():
#             print('Key: ', key)
#             print('Value: ', obj.annotations[key])
#         print('*' * 20)
#
#
# def print_annotations_of_object(obj):
#     for key in obj.annotations.keys():
#         print('Key: ', key)
#         print('Value: ', obj.annotations[key])
#     print('*' * 20)
#
#
# def print_attributes_of_object(object):
#     attribs = object._all_attrs
#     # print(attribs)
#     for attrib in attribs:
#         if attrib[0] is not 'signal':
#             print(attrib[0], ': ', object.__getattribute__(attrib[0]))
#         else:
#             print(attrib[0], ': ', object[:])
#         print('*' * 10)
#     print('*' * 20)
#
#
# def print_attributes_of_all_objects(block, objtype):
#     objects = block.list_children_by_class(objtype)
#     index = 0
#     for object in objects:
#         print('                                       *****Number: ', index)
#         # print_attributes_of_object(object)
#         index = index + 1
#         print('ANASIG FROM CHANIND: ', object.analogsignals[0][object.index[0]])
#     print_attributes_of_object(block)
#
#
# def child_objects(block, objtype):
#     return block.list_children_by_class(objtype)
#
#
# def chanind_anasig_relation(block):  # GOOD
#     chaninds = block.list_children_by_class(ChannelIndex)
#     for chanind in chaninds:
#         print(chanind.name)
#         anasigs = chanind.analogsignals
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.channel_index.name)
#         units = chanind.units
#         for unit in units:
#             print(unit.name)
#         print('*' * 10)
#
#
# def chanind_unit_relation(block):  # GOOD
#     chaninds = block.list_children_by_class(ChannelIndex)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.units
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.channel_index)
#         units = chanind.units
#
#         print('*' * 10)
#
#
# def unit_st_relation(block):
#     chaninds = block.list_children_by_class(Unit)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.spiketrains
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.unit)
#         print('*' * 10)
#
#
# def st_unit_relation(block):
#     chaninds = block.list_children_by_class(SpikeTrain)
#     for chanind in chaninds:
#         print(chanind)
#         anasig = chanind.unit
#         try:
#             print(anasig.name, 'ChannelIndex: ', anasig.spiketrains)
#         except:
#             print("No Unit linked to this SpikeTrain")
#         print('*' * 10)
#
#
# def segment_anasig_relation(block):
#     chaninds = block.list_children_by_class(Segment)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.analogsignals
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.segment)
#         print('*' * 10)
#
#
# def segment_st_relation(block):
#     chaninds = block.list_children_by_class(Segment)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.spiketrains
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.segment)
#         print('*' * 10)
#
#
# def segment_epoch_relation(block):
#     chaninds = block.list_children_by_class(Segment)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.epochs
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.segment)
#         print('*' * 10)
#
#
# def segment_event_relation(block):
#     chaninds = block.list_children_by_class(Segment)
#     for chanind in chaninds:
#         print(chanind)
#         anasigs = chanind.events
#         for anasig in anasigs:
#             print(anasig.name, 'ChannelIndex: ', anasig.segment)
#         print('*' * 10)
#
#
# def block_chanind_relation(block):
#     print(block)
#     anasigs = block.channel_indexes
#     for anasig in anasigs:
#         print(anasig.name, 'ChannelIndex: ', anasig.block)
#     print('*' * 10)
#
#
# def block_segment_relation(block):
#     print(block)
#     anasigs = block.segments
#     for anasig in anasigs:
#         print(anasig.name, 'ChannelIndex: ', anasig.block)
#     print('*' * 10)
#
#
# def compare_array_content(rescale_factor, array1, array2):
#     array1 = (array1 / rescale_factor).magnitude
#     array2 = array2.magnitude
#     print(array1, array2)
#     if np.allclose(array1, array2, atol=0.000000000000000001):
#         print('Good')
#     else:
#         print('Failed')
#
#
# def compare_object_content(old_block, new_block, objtype):
#     objolds = old_block.list_children_by_class(objtype)
#     objnews = new_block.list_children_by_class(objtype)
#     for objold, objnew in zip(objolds, objnews):
#         oldarray = objold.times  # specific for SpikeTrain and Event
#         newarray = objnew[:]  # specific for AnaSig
#         compare_array_content(oldarray[0] / newarray[0], oldarray, newarray)
#
#
# def run_test():
#     old_block = old_brio_load()
#     # output(old_block)
#     new_block = new_brio_load()
#     # output(new_block)
#     # compare_neo_content(old_block, new_block)
#     # print('OLD IO')
#     # print_annotations_id(old_block, 'SpikeTrain')
#     # print('NEW IO')
#     # print_annotations_id(new_block, 'SpikeTrain')
#     # chan_ind = child_objects(old_block, ChannelIndex)
#     # print('NEW Event Annotations')
#     # print_annotations_all(new_block, Event)
#     # print('NEW Epoch Attributes')        # NEED TO DO THIS FOR AAAAALLLLLL OBJECT TYPES!!!!!!!!!!!!!! Unit SpikeTrain Event Epoch
#     # print_attributes_of_all_objects(old_block, ChannelIndex)
#     # print_attributes_of_all_objects(new_block, ChannelIndex)
#     # chanind_anasig_relation(new_block)
#     # chanind_unit_relation(new_block)
#     # unit_st_relation(new_block)
#     # st_unit_relation(old_block)
#     # segment_anasig_relation(old_block)
#     # segment_st_relation(new_block)
#     # segment_event_relation(new_block)
#     # block_segment_relation(new_block)
#     # compare_object_content(old_block, new_block, AnalogSignal)
#     # print_annotations_id(new_block, Unit)
#     # print_annotations_id()
#     # print_attributes_of_object(new_block)
#     # print_attributes_of_object(old_block)
#     # print_annotations_of_object(new_block)
#     print_annotations_of_object(old_block)
#     anasig = new_block.list_children_by_class(AnalogSignal)[2]
#     print anasig.shape
#
#
# run_test()
outputComparison.compare(old_brio_load(), new_brio_load())
