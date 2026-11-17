from example_server.project_search import build_search_filters


def test_no_filters_searches_entire_inventory():
    filters, where_clause, parameters = build_search_filters()

    assert filters.model_dump() == {
        "query": None,
        "agency": None,
        "organization": None,
    }
    assert where_clause == ""
    assert parameters == []


def test_filters_preserve_values_and_bind_them_separately():
    filters, where_clause, parameters = build_search_filters(
        query=" documents ",
        agency=" HHS ",
        organization=" CMS ",
    )

    assert filters.query == "documents"
    assert filters.agency == "HHS"
    assert filters.organization == "CMS"
    assert parameters == ["documents", "documents", "HHS", "CMS"]
    assert "OR contains" in where_clause
    assert "AND agency = ?" in where_clause
    assert "AND organization = ?" in where_clause
    assert "documents" not in where_clause
    assert "HHS" not in where_clause


def test_blank_filters_become_no_restriction():
    filters, where_clause, parameters = build_search_filters(
        query=" ",
        agency="",
        organization="\t",
    )

    assert filters.query is None
    assert filters.agency is None
    assert filters.organization is None
    assert where_clause == ""
    assert parameters == []


def test_special_characters_remain_parameter_values():
    query = "100%_coverage' OR 1=1 --"

    filters, where_clause, parameters = build_search_filters(query=query)

    assert filters.query == query
    assert parameters == [query, query]
    assert query not in where_clause
    assert "LIKE" not in where_clause.upper()
