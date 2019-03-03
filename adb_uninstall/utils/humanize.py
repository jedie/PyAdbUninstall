def human_duration(t):
    """
    Converts a time duration into a friendly text representation.

    >>> human_duration(datetime.timedelta(microseconds=1000))
    '1.0 ms'
    >>> human_duration(0.01)
    '10.0 ms'
    >>> human_duration(0.9)
    '900.0 ms'
    >>> human_duration(datetime.timedelta(seconds=1))
    '1.0 sec'
    >>> human_duration(65.5)
    '1.1 min'
    >>> human_duration(59.1 * 60)
    '59.1 min'
    """
    if t < 1:
        return "%.1f ms" % round(t * 1000, 1)
    if t < 60:
        return "%.1f sec" % round(t, 1)
    return "%.1f min" % round(t / 60, 1)
