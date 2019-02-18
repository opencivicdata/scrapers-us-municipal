import pytest

@pytest.mark.parametrize('field,value,assertion', [
    ('MatterRestrictViewViaWeb', False, None),
    ('MatterRestrictViewViaWeb', True, True),
    ('MatterStatusName', 'Draft', True),
    ('MatterStatusName', 'Passed', None),
    ('legistar_url', None, True),
])
def test_is_restricted(scraper, matter, field, value, assertion):
    '''
    Unit test for `_is_restricted` function on bill scraper.
    '''
    matter[field] = value

    assert scraper._is_restricted(matter) == assertion
    