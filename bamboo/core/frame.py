from cStringIO import StringIO

from pandas import Series

from bamboo.lib.mongo import MONGO_ID_ENCODED


# reserved bamboo keys
BAMBOO_RESERVED_KEY_PREFIX = '^^'
DATASET_ID = BAMBOO_RESERVED_KEY_PREFIX + 'dataset_id'
INDEX = BAMBOO_RESERVED_KEY_PREFIX + 'index'
PARENT_DATASET_ID = BAMBOO_RESERVED_KEY_PREFIX + 'parent_dataset_id'

BAMBOO_RESERVED_KEYS = [
    DATASET_ID,
    INDEX,
    PARENT_DATASET_ID,
]

# all the reserved keys
RESERVED_KEYS = BAMBOO_RESERVED_KEYS + [MONGO_ID_ENCODED]


def add_id_column(df, dataset_id):
    return add_constant_column(df, dataset_id, DATASET_ID) if not\
        DATASET_ID in df.columns else df


def add_constant_column(df, value, name):
    column = Series([value] * len(df), index=df.index, name=name)
    return df.join(column)


def add_parent_column(df, parent_dataset_id):
    """Add parent ID column to this DataFrame."""
    return add_constant_column(df, parent_dataset_id, PARENT_DATASET_ID)


def df_to_csv_string(df):
    buffer = StringIO()
    df.to_csv(buffer, encoding='utf-8', index=False)
    return buffer.getvalue()


def join_dataset(left, other, on):
    """Left join an `other` dataset.

    :param other: Other dataset to join.
    :param on: Column or 2 comma seperated columns to join on.

    :returns: Joined DataFrame.

    :raises: `KeyError` if join columns not in datasets.
    """
    on_lhs, on_rhs = (on.split(',') * 2)[:2]

    right_dframe = other.dframe(padded=True)

    if on_lhs not in left.columns:
        raise KeyError('No item named "%s" in left hand side dataset' % on_lhs)

    if on_rhs not in right_dframe.columns:
        raise KeyError('No item named "%s" in right hand side dataset' %
                       on_rhs)

    right_dframe = right_dframe.set_index(on_rhs)

    if len(right_dframe.index) != len(right_dframe.index.unique()):
        msg = 'Join column "%s" of the right hand side dataset is not unique'
        raise NonUniqueJoinError(msg % on_rhs)

    shared_columns = left.columns.intersection(right_dframe.columns)

    if len(shared_columns):
        rename_map = [{c: '%s.%s' % (c, v) for c in shared_columns} for v
                      in ['x', 'y']]
        left.rename(columns=rename_map[0], inplace=True)
        right_dframe.rename(columns=rename_map[1], inplace=True)

    return left.join(right_dframe, on=on_lhs)


def remove_reserved_keys(df, exclude=[]):
    """Remove reserved internal columns in this DataFrame.

    :param keep_parent_ids: Keep parent column if True, default False.
    """
    reserved_keys = __column_intersect(
        df, BAMBOO_RESERVED_KEYS).difference(set(exclude))

    return df.drop(reserved_keys, axis=1)


def rows_for_parent_id(df, parent_id):
    """DataFrame with only rows for `parent_id`.

    :param parent_id: The ID to restrict rows to.

    :returns: A DataFrame including only rows with a parent ID equal to
        that passed in.
    """
    return df[df[PARENT_DATASET_ID] == parent_id].drop(PARENT_DATASET_ID, 1)


def __column_intersect(df, list_):
    """Return the intersection of `list_` and DataFrame's columns."""
    return set(list_).intersection(set(df.columns.tolist()))


class NonUniqueJoinError(Exception):
    pass
