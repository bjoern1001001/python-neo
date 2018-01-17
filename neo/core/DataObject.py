"""Basic functionality for all data objects that inherit from pq.Quantity"""

import quantities as pq

from neo.core.baseneo import BaseNeo


class DataObject(BaseNeo, pq.Quantity):

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