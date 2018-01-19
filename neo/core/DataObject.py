"""Basic functionality for all data objects that inherit from pq.Quantity"""

import quantities as pq
import numpy as np

from neo.core.baseneo import BaseNeo


class DataObject(BaseNeo, pq.Quantity):

    def _check_annotations(self, value):
        for key in value:
            #if not isinstance(value[key], (list, np.ndarray)):
            #    raise ValueError("Annotations need to be a list or an array")
            #try:
            #    length = self.shape[1]
            #except IndexError:
            #    length = 1
            #if not length == len(value[key]):
            #   raise ValueError("Incorrect length of array annotation")
            #for a in value[key]:
             #   if isinstance(a, np.ndarray):
              #      raise ValueError("")    # TODO: Should annotations only be 1-dimensional?
                BaseNeo._check_annotations(self, value[key])

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
