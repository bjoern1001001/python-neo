"""Basic functionality for all data objects that inherit from pq.Quantity"""

import quantities as pq
import numpy as np

from neo.core.baseneo import BaseNeo


class DataObject(BaseNeo, pq.Quantity):

    def _check_annotations(self, value):        # TODO: Is there anything else that can be checked here?

        # First stage, resolve dict of annotations into single annotations
        if isinstance(value, dict):
            for key in value.keys():
                if isinstance(value[key], dict):
                    raise ValueError("Dicts are not allowed as annotations")    # TODO: Is this really the case?
                value[key] = self._check_annotations(value[key])

        # If not array annotation, pass on to regular check
        elif not isinstance(value, (list, np.ndarray)):
            BaseNeo._check_annotations(self, value)

        # If array annotation, check for correct length, only single dimension and
        else:
            try:
                own_length = self.shape[1]
            except IndexError:
                own_length = 1

            # Escape check if empty array or list
            if len(value) == 0:
                val_length = own_length
            else:
                # Note: len(o) also works for np.ndarray, it then uses the outmost dimension,
                # which is exactly the desired behaviour here
                val_length = len(value)

            if not own_length == val_length:
                raise ValueError("Incorrect length of array annotation")

            for element in value:
                if isinstance(element, (list, np.ndarray)):
                    raise ValueError("Array annotations should only be 1-dimensional")

                BaseNeo._check_annotations(self, value)

            if isinstance(value, list):
                value = np.array(value)

        return value

    def annotations_at_index(self, index):  # TODO: Should they be sorted by key (current) or index?

        index_annotations = {}

        # Use what is given as an index to determine the corresponding annotations,
        # if not possible, numpy raises an Error
        for ann in self.annotations.keys():
            index_annotations[ann] = self.annotations[ann][index]

        return index_annotations

    def as_array(self, units=None):
        """
        Return the object's data as a plain NumPy array.

        If `units` is specified, first rescale to those units.
        """
        if units:
            return self.rescale(units).magnitude
        else:
            return self.magnitude

    def as_quantity(self):
        """
        Return the spike times as a quantities array.
        """
        return self.view(pq.Quantity)
