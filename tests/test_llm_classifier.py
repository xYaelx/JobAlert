import pytest
import llm_classifier
from llm_classifier import load_profile, build_system_prompt, JOB_LABELS, SYSTEM_PROMPT_TEMPLATE

real_load_profile = load_profile


def test_load_profile_reads_file(tmp_path):
    profile_file = tmp_path / "profile.txt"
    profile_file.write_text("  NLP engineer, 4 years, Berlin  \n", encoding="utf-8")
    assert load_profile(profile_file) == "NLP engineer, 4 years, Berlin"


def test_load_profile_missing_file_points_to_example(tmp_path):
    with pytest.raises(FileNotFoundError, match="profile.example.txt"):
        load_profile(tmp_path / "profile.txt")


def test_example_profile_is_loadable():
    assert load_profile("profile.example.txt")


def test_system_prompt_includes_profile_and_labels():
    prompt = build_system_prompt("NLP engineer, 4 years, Berlin")
    assert "NLP engineer, 4 years, Berlin" in prompt
    for label in JOB_LABELS:
        assert label in prompt


# Clearly synthetic profile for tests; not anyone's real data
SYNTHETIC_PROFILE = (
    "Role: SYNTHETIC TEST PERSONA - underwater basket-weaving vision engineer\n"
    "Experience: 42 years of Fortran 77\n"
    "Location: Atlantis (remote from the Moon)"
)


def test_classifier_loads_profile_at_runtime(tmp_path, monkeypatch):
    profile_file = tmp_path / "profile.txt"
    profile_file.write_text(SYNTHETIC_PROFILE, encoding="utf-8")
    monkeypatch.setattr(llm_classifier, "load_profile", lambda: real_load_profile(profile_file))
    monkeypatch.setattr(llm_classifier, "GPT_API_KEY", "test-key-not-real")

    classifier = llm_classifier.OpenAIClassifier()

    assert SYNTHETIC_PROFILE in classifier.system_prompt


def test_profile_appears_only_at_the_template_placeholder():
    # The tracked template must not hard-code profile details; the profile
    # supplied at runtime is inserted only where {profile} stands
    prompt = build_system_prompt(SYNTHETIC_PROFILE)
    assert SYSTEM_PROMPT_TEMPLATE.count("{profile}") == 1
    assert prompt.replace(SYNTHETIC_PROFILE, "{profile}") == SYSTEM_PROMPT_TEMPLATE
    profile_section = SYSTEM_PROMPT_TEMPLATE.split("Candidate profile:\n", 1)[1].split("\n\n", 1)[0]
    assert profile_section == "{profile}"
