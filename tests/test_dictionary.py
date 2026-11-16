import pytest
from app.dictionary import parse_dictionary, first_definition, decode_saved


def test_multi_part_of_speech():
    data = parse_dictionary([{'word':'implement','meanings':[
        {'partOfSpeech':'noun','definitions':[{'definition':'A tool.'}]},
        {'partOfSpeech':'verb','definitions':[{'definition':'To carry out a plan.','example':'Implement the plan.'}]}
    ]}], 'implement')
    assert [x['partOfSpeech'] for x in data['meanings']] == ['noun','verb']
    assert first_definition(data) == 'A tool.'
    assert data['meanings'][1]['definitions'][0]['example'] == 'Implement the plan.'


def test_missing_example_is_empty():
    data = parse_dictionary([{'meanings':[{'partOfSpeech':'noun','definitions':[{'definition':'Confidence.'}]}]}], 'audacity')
    assert data['meanings'][0]['definitions'][0]['example'] == ''
    assert decode_saved('old free text') is None
