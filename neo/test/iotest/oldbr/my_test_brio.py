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

from neo.test.iotest.common_io_test import BaseTestIO
from neo.test.iotest.tools import get_test_file_full_path

#################
# from __future__ import absolute_import

import os
import sys
import re
import warnings

import unittest

import numpy as np
import quantities as pq

from neo.test.iotest.common_io_test import BaseTestIO
from neo.core import *

from neo.io.neuralynxio import NewNeuralynxIO
from neo.io.neuralynxio import NeuralynxIO as OldNeuralynxIO
from neo import AnalogSignal

import time

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


# old_block = None
# new_block = None
def old_brio_load():
    # ioclass = old_brio
    # files_to_test = ['FileSpec2.3001']
    oldbrio_reader = old_brio(dirname)
    old_block = oldbrio_reader.read_block(
        # n_starts=[None], n_stops=None,
        channels={1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 129, 130},
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


def output(block):
    for seg in block.segments:
        print('seg', seg.index)
        for anasig in seg.analogsignals:
            print(' AnalogSignal', anasig.name, anasig.shape, anasig.t_start, anasig.sampling_rate)
            print('ChannelIndex', anasig.annotations['channel_id'])
            # print(anasig.channel_index.channel_id) => SHOULD WORK; BUT DOESN'T!!!!!!!!!!!
        for st in seg.spiketrains:
            if st is not None:
                print(' SpikeTrain', st.name, st.shape, st.waveforms.shape, st.rescale(pq.s)[:5])
        for ev in seg.events:
            print(' Event', ev.name, ev.times.shape)
    print ('*' * 10)


# def count_channels(block):
#     num_channels = 0
#     for seg in block.segments:
#         for anasig in seg.analogsignals:
#             a = block.annotations

def compare_neo_content(bl1, bl2):
    print('*' * 5, 'Comparison of blocks', '*' * 5)
    object_types_to_test = [Segment, ChannelIndex, Unit, AnalogSignal,
                            SpikeTrain, Event, Epoch]
    # object_types_to_test = [SpikeTrain]
    for objtype in object_types_to_test:
        print('Testing {}'.format(objtype))
        children1 = bl1.list_children_by_class(objtype)
        children2 = bl2.list_children_by_class(objtype)

        if len(children1) != len(children2):
            warnings.warn('Number of {} is different in both blocks ({} != {'
                          '}). Skipping comparison'.format(objtype,
                                                           len(children1),
                                                           len(children2)))
            continue

        for child1, child2 in zip(children1, children2):
            compare_annotations(child1.annotations, child2.annotations, objtype)
            # compare_attributes(child1, child2)


def compare_failing_classes(old_block,
                            new_block):  # more precise comparison of the classes that fail compare_neo_content, here AnaSig, Event and ChannelIndex
    print('*')


def compare_annotations(anno1, anno2, objecttype):
    if len(anno1) != len(anno2):
        warnings.warn('Different numbers of annotations! {} != {'
                      '}\nSkipping further comparison of this '
                      'annotation list.'.format(
            anno1.keys(), anno2.keys()))
        print('In:', objecttype)
        time.sleep(5)
        return
    assert anno1.keys() == anno2.keys()
    for key in anno1.keys():
        anno1[key] = anno2[key]


def print_annotations_id(block,
                         objtype):  # because comparison will always say false, so need to check content => for IDs
    children1 = block.list_children_by_class(objtype)
    for child1 in children1:
        try:  # => if 'Unit_id' in child1.annotations   [.keys] => raus!!!
            print('Unit_ID:', child1.annotations['unit_id'])
        except:
            pass
        try:
            print('Channel_ID:', child1.annotations['channel_id'])
        except:
            pass
        try:
            print('ID:', child1.annotations['id'])
        except:
            pass
    print('*' * 10)


def print_annotations_all(
        block,
        objtype):
    objects = block.list_children_by_class(objtype)
    print ('Object Type: ', objtype)
    for obj in objects:
        for key in obj.annotations.keys():
            print('Key: ', key)
            print('Value: ', obj.annotations[key])
        print('*' * 20)


def print_attributes_of_object(object):
    attribs = object._all_attrs
    #print(attribs)
    for attrib in attribs:
        if attrib[0] is not 'signal':
            print(attrib[0], ': ', object.__getattribute__(attrib[0]))
        else:
            print(attrib[0], ': ', object[:])
        print('*' * 10)
    print('*' * 20)


def print_attributes_of_all_objects(block, objtype):
    objects = block.list_children_by_class(objtype)
    index = 0
    for object in objects:
        print('                                       *****Number: ', index)
        print_attributes_of_object(object)
        index = index + 1


def child_objects(block, objtype):
    return block.list_children_by_class(objtype)


def run_test():
    old_block = old_brio_load()
    output(old_block)
    new_block = new_brio_load()
    #output(new_block)
    #compare_neo_content(old_block, new_block)
    # print('OLD IO')
    # print_annotations_id(old_block, 'SpikeTrain')
    # print('NEW IO')
    # print_annotations_id(new_block, 'SpikeTrain')
    # chan_ind = child_objects(old_block, ChannelIndex)
    # print('NEW Event Annotations')
    # print_annotations_all(new_block, Event)
    #print('NEW Epoch Attributes')        # NEED TO DO THIS FOR AAAAALLLLLL OBJECT TYPES!!!!!!!!!!!!!! Unit SpikeTrain Event Epoch
    #print_attributes_of_all_objects(old_block, AnalogSignal)    # #Signal cannot be found in AnaSig, for old and new


run_test()
