from chunk_viewer.section_paths import clean_heading, fix_section_paths

S202 = "Section 202 – Accessory Uses, Buildings and Structures"


def test_rural_transect_becomes_a_group_not_a_sibling():
    # What pymupdf4llm produces for s.202: "Rural Transect" (16pt) lands at the same depth as
    # its subheadings, so the rural provisions keep "Urban Transects" as their parent.
    raw = [
        [S202],
        [S202, "Urban Transects"],
        [S202, "Urban Transects", "Maximum Number of Accessory Buildings"],
        [S202, "Urban Transects", "Minimum Required Setback from a Lot Line"],
        [S202, "Urban Transects", "Rural Transect"],
        [S202, "Urban Transects", "Maximum Number of Accessory Buildings"],
        [S202, "Urban Transects", "Maximum Permitted Height"],
        ["Section 203 – Projections Above the Height Limit"],
    ]
    fixed = fix_section_paths(raw)
    assert fixed[2] == [S202, "Urban Transects", "Maximum Number of Accessory Buildings"]
    assert fixed[4] == [S202, "Rural Transect"]
    assert fixed[5] == [S202, "Rural Transect", "Maximum Number of Accessory Buildings"]
    assert fixed[6] == [S202, "Rural Transect", "Maximum Permitted Height"]
    assert fixed[7] == ["Section 203 – Projections Above the Height Limit"]


def test_continuation_chunks_keep_their_heading():
    raw = [
        [S202, "Rural Transect"],
        [S202, "Rural Transect", "Maximum Permitted Size"],
        [S202, "Rural Transect", "Maximum Permitted Size"],  # chunk with no heading of its own
    ]
    assert fix_section_paths(raw)[2] == [S202, "Rural Transect", "Maximum Permitted Size"]


def test_subheading_without_group_sits_under_section():
    raw = [["Section 204 – Projections into Yards", "Provisions for Specific Features"]]
    assert fix_section_paths(raw) == [raw[0]]


def test_clean_heading_strips_markdown():
    assert clean_heading("Additional Dwelling Unit** means:") == "Additional Dwelling Unit means:"
