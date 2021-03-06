# pylint: disable-msg=W0612

from datetime import datetime
import unittest

from numpy.random import randn
import numpy as np

from pandas.core.api import Index, Series, DataMatrix, DataFrame, isnull

import pandas.util.testing as common
import test_frame

#-------------------------------------------------------------------------------
# DataMatrix test cases

class TestDataMatrix(test_frame.TestDataFrame):
    klass = DataMatrix

    def test_more_constructor(self):
        arr = randn(10)
        dm = self.klass(arr, columns=['A'], index=np.arange(10))
        self.assertEqual(dm.values.ndim, 2)

        arr = randn(0)
        dm = self.klass(arr)
        self.assertEqual(dm.values.ndim, 2)
        self.assertEqual(dm.values.ndim, 2)

        # no data specified
        dm = self.klass(columns=['A', 'B'], index=np.arange(10))
        self.assertEqual(dm.values.shape, (10, 2))

        dm = self.klass(columns=['A', 'B'])
        self.assertEqual(dm.values.shape, (0, 2))

        dm = self.klass(index=np.arange(10))
        self.assertEqual(dm.values.shape, (10, 0))

        # corner, silly
        self.assertRaises(Exception, self.klass, (1, 2, 3))

        # can't cast
        mat = np.array(['foo', 'bar'], dtype=object).reshape(2, 1)
        df = DataMatrix(mat, index=[0, 1], columns=[0], dtype=float)
        self.assert_(df.values.dtype == np.object_)

        dm = self.klass(DataFrame(self.frame._series))
        common.assert_frame_equal(dm, self.frame)

        # int cast
        dm = DataMatrix({'A' : np.ones(10, dtype=int),
                         'B' : np.ones(10, dtype=float)},
                        index=np.arange(10))

        self.assertEqual(len(dm.columns), 2)
        self.assert_(dm.values.dtype == np.float_)

    def test_constructor_with_objects(self):
        index = self.mixed_frame.index[:5]

        dm = DataMatrix(data=None, index=index,
                        objects=self.mixed_frame.objects)
        self.assert_(dm.index is index)
        self.assert_(dm.objects.index is index)

        dm = DataMatrix(data=None, index=index,
                        objects=self.mixed_frame.objects._series)
        self.assert_(dm.index is index)
        self.assert_(dm.objects.index is index)

        index = self.mixed_frame.index
        dm = DataMatrix(data=None, index=index,
                        objects=self.mixed_frame.objects)
        self.assert_(dm.index is index)
        self.assert_(dm.objects.index is index)

        index = self.mixed_frame.index
        dm = DataMatrix(objects=self.mixed_frame.objects)
        self.assert_(dm.index is self.mixed_frame.index)

        # take dict of objects
        index = self.mixed_frame.index
        dm = DataMatrix(data={}, objects=self.mixed_frame.objects._series)
        self.assert_(isinstance(dm.objects, DataMatrix))
        self.assert_(dm.index is dm.objects.index)

        index = self.mixed_frame.index
        dm = DataMatrix(objects=self.mixed_frame.objects._series)
        self.assert_(isinstance(dm.objects, DataMatrix))
        self.assert_(dm.index is dm.objects.index)

        index = self.mixed_frame.index
        dm = DataMatrix(data=self.frame._series,
                        objects=self.mixed_frame.objects._series)
        self.assert_(isinstance(dm.objects, DataMatrix))
        self.assert_(dm.objects.columns.equals(
                self.mixed_frame.objects.columns))

        objs = DataMatrix({'bar' : ['bar'] * len(self.mixed_frame)})
        dm = DataMatrix(self.mixed_frame._series, objects=objs)
        self.assert_('foo' in dm.objects)

    def test_constructor_objects_corner(self):
        obj = {'A' : {1 : '1', 2 : '2'}}
        obj_dm = DataMatrix(obj)
        mat = np.zeros((3, 3), dtype=float)

        dm = DataMatrix(mat, index=[1, 2, 3], columns=['B', 'C', 'D'],
                        objects=obj_dm)
        assert dm.index is not obj_dm.index

        dm = DataMatrix(mat, index=[1, 2, 3], columns=['B', 'C', 'D'],
                        objects=obj)

        dm = DataMatrix(index=[1, 2, 3], objects=obj_dm)
        dm = DataMatrix(index=[1, 2, 3], objects=obj)

    def test_copy(self):
        # copy objects
        copy = self.mixed_frame.copy()
        self.assert_(copy.objects is not self.mixed_frame.objects)

    def test_combineFirst_mixed(self):
        a = Series(['a','b'], index=range(2))
        b = Series(range(2), index=range(2))
        f = DataMatrix({'A' : a, 'B' : b})

        a = Series(['a','b'], index=range(5, 7))
        b = Series(range(2), index=range(5, 7))
        g = DataMatrix({'A' : a, 'B' : b})

        combined = f.combineFirst(g)

    def test_setitem_corner(self):
        # corner case
        df = self.klass({'B' : [1., 2., 3.],
                         'C' : ['a', 'b', 'c']},
                        index=np.arange(3))
        del df['B']
        df['B'] = [1., 2., 3.]
        self.assert_('B' in df)
        self.assertEqual(len(df.columns), 1)

        df['A'] = 'beginning'
        df['E'] = 'foo'
        df['D'] = 'bar'
        df[datetime.now()] = 'date'
        df[datetime.now()] = 5.

        # what to do when empty frame with index
        dm = DataMatrix(index=self.frame.index)
        dm['A'] = 'foo'
        dm['B'] = 'bar'
        self.assertEqual(len(dm.objects.columns), 2)

        dm['C'] = 1
        self.assertEqual(len(dm.columns), 1)

        # set existing column
        dm['A'] = 'bar'
        self.assertEqual('bar', dm['A'][0])

        dm = DataMatrix(index=np.arange(3))
        dm['A'] = 1
        dm['foo'] = 'bar'
        del dm['foo']
        dm['foo'] = 'bar'
        self.assertEqual(len(dm.objects.columns), 1)

    def test_setitem_ambig(self):
        # difficulties with mixed-type data
        from decimal import Decimal

        # created as float type
        dm = DataMatrix(index=range(3), columns=range(3))

        coercable_series = Series([Decimal(1) for _ in range(3)],
                                  index=range(3))
        uncoercable_series = Series(['foo', 'bzr', 'baz'], index=range(3))

        dm[0] = np.ones(3)
        self.assertEqual(len(dm.cols()), 3)
        self.assert_(dm.objects is None)

        dm[1] = coercable_series
        self.assertEqual(len(dm.cols()), 3)
        self.assert_(dm.objects is None)

        dm[2] = uncoercable_series
        self.assertEqual(len(dm.cols()), 3)
        self.assert_(dm.objects is not None)
        self.assert_(2 in dm.objects)
        self.assert_(2 not in dm.columns)

    def test_delitem_corner(self):
        f = self.frame.copy()
        del f['D']
        self.assertEqual(len(f.columns), 3)
        self.assertRaises(KeyError, f.__delitem__, 'D')
        del f['B']
        self.assertEqual(len(f.columns), 2)

    def test_shift_objects(self):
        tsf = self.tsframe.copy()
        tsf['foo'] = 'bar'

        shifted = tsf.shift(1)
        self.assert_(shifted.objects is not None)
        self.assert_(shifted.objects.index is shifted.index)

    def test_more_asMatrix(self):
        values = self.mixed_frame.asMatrix()
        self.assertEqual(values.shape[1], len(self.mixed_frame.cols()))

    def test_reindex_bool(self):
        frame = DataMatrix(np.ones((10, 2), dtype=bool),
                           index=np.arange(0, 20, 2),
                           columns=[0, 2])

        reindexed = frame.reindex(np.arange(10))
        self.assert_(reindexed.values.dtype == np.float_)
        self.assert_(np.isnan(reindexed[0][1]))

        reindexed = frame.reindex(columns=range(3))
        self.assert_(reindexed.values.dtype == np.float_)
        self.assert_(isnull(reindexed[1]).all())

    def test_reindex_objects(self):
        reindexed = self.mixed_frame.reindex(columns=['foo', 'A', 'B'])
        self.assert_('foo' in reindexed)

        reindexed = self.mixed_frame.reindex(columns=['A', 'B'])
        self.assert_('foo' not in reindexed)

    def test_reindex_corner(self):
        index = Index(['a', 'b', 'c'])
        dm = self.empty.reindex(index=[1, 2, 3])
        reindexed = dm.reindex(columns=index)
        self.assert_(reindexed.columns.equals(index))

        # ints are weird

        smaller = self.intframe.reindex(columns=['A', 'B', 'E'])
        self.assert_(smaller['E'].dtype == np.float_)

    def test_rename_objects(self):
        renamed = self.mixed_frame.rename(columns=str.upper)
        self.assert_('FOO' in renamed)
        self.assert_('foo' not in renamed)

    def test_fill_corner(self):
        self.mixed_frame['foo'][5:20] = np.NaN
        self.mixed_frame['A'][-10:] = np.NaN

        obj_result = self.mixed_frame.objects.fillna(value=0)

        del self.mixed_frame['foo']

        # XXX
        obj_result = self.mixed_frame.objects.fillna(value=0)

	empty_float = self.frame.reindex(columns=[])
        result = empty_float.fillna(value=0)

    def test_count_objects(self):
        dm = DataMatrix(self.mixed_frame._series)
        df = DataFrame(self.mixed_frame._series)

        common.assert_series_equal(dm.count(), df.count())
        common.assert_series_equal(dm.count(1), df.count(1))

    def test_cumsum_corner(self):
        dm = DataMatrix(np.arange(20).reshape(4, 5),
                        index=range(4), columns=range(5))
        result = dm.cumsum()

if __name__ == '__main__':
    unittest.main()
