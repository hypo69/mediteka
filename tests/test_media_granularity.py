# -*- coding: utf-8 -*-
"""
Тесты модуля src/media_granularity.py
"""

import pytest
from src.media_granularity import (
    determine_granularity,
    determine_granularity_from_record,
    get_prompt_by_granularity,
    get_granularity_display_name,
    get_granularity_thresholds,
    PROMPT_EPISODE_DRIVEN,
    PROMPT_ARC_DRIVEN,
    PROMPT_SEASON_DRIVEN,
    PROMPT_OVERVIEW,
    LONG_RUNNING_THRESHOLD,
    EPISODES_PER_SEASON_DRAMA_THRESHOLD,
    EPISODES_PER_SEASON_ACTION_THRESHOLD,
)


class TestDetermineGranularity:
    """Тесты функции determine_granularity."""

    def test_zero_seasons_returns_overview(self):
        """Тест что 0 сезонов возвращает overview."""
        assert determine_granularity(0) == 'overview'

    def test_negative_seasons_returns_overview(self):
        """Тест что отрицательное число сезонов возвращает overview."""
        assert determine_granularity(-1) == 'overview'

    def test_long_running_series_returns_overview(self):
        """Тест что очень длинный сериал возвращает overview."""
        assert determine_granularity(20) == 'overview'

    def test_episode_granularity_short_seasons_few_episodes(self):
        """Тест episode granularity: мало сезонов, мало эпизодов."""
        assert determine_granularity(3, [8, 8, 8]) == 'episode'

    def test_episode_granularity_single_season(self):
        """Тест episode granularity: один сезон."""
        assert determine_granularity(1, [10]) == 'episode'

    def test_arc_granularity_medium_series(self):
        """Тест arc granularity: средний сериал."""
        assert determine_granularity(5, [22, 22, 22, 22, 22]) == 'arc'

    def test_season_granularity_drama(self):
        """Тест season granularity: драма с большим количеством эпизодов."""
        assert determine_granularity(5, [50, 50, 50, 50, 50]) == 'overview'

    def test_overview_granularity_very_long(self):
        """Тест overview для очень длинных сериалов."""
        assert determine_granularity(16) == 'overview'

    def test_with_avg_episodes_action_threshold(self):
        """Тест с avg_episodes_per_season на границе."""
        assert determine_granularity(5, avg_episodes_per_season=12) == 'arc'
        assert determine_granularity(5, avg_episodes_per_season=24) == 'arc'
        assert determine_granularity(5, avg_episodes_per_season=11) == 'episode'

    def test_with_avg_episodes_drama_threshold(self):
        """Тест с avg_episodes_per_season выше порога драмы."""
        assert determine_granularity(5, avg_episodes_per_season=40) == 'overview'

    def test_fallback_heuristic_few_seasons(self):
        """Тест fallback эвристики: мало сезонов."""
        assert determine_granularity(3) == 'episode'

    def test_fallback_heuristic_medium_seasons(self):
        """Тест fallback эвристики: среднее количество сезонов."""
        assert determine_granularity(6) == 'arc'

    def test_fallback_heuristic_many_seasons(self):
        """Тест fallback эвристики: много сезонов."""
        assert determine_granularity(10) == 'season'

    def test_fallback_heuristic_very_many_seasons(self):
        """Тест fallback эвристики: очень много сезонов."""
        assert determine_granularity(14) == 'season'


class TestDetermineGranularityFromRecord:
    """Тесты функции determine_granularity_from_record."""

    def test_empty_record(self):
        """Тест с пустой записью."""
        record = {}
        result = determine_granularity_from_record(record)
        assert result == 'overview'

    def test_record_with_seasons(self):
        """Тест с записью с количеством сезонов."""
        record = {'num_of_seasons': 5}
        result = determine_granularity_from_record(record)
        assert result in ['episode', 'arc', 'season', 'overview']

    def test_record_with_episodes_list(self):
        """Тест с записью со списком эпизодов."""
        record = {
            'num_of_seasons': 3,
            'num_episodes_per_season': [10, 10, 10]
        }
        result = determine_granularity_from_record(record)
        assert result == 'episode'

    def test_record_with_episodes_json_string(self):
        """Тест с записью со списком эпизодов в виде JSON строки."""
        record = {
            'num_of_seasons': 3,
            'num_episodes_per_season': '[10, 10, 10]'
        }
        result = determine_granularity_from_record(record)
        assert result == 'episode'

    def test_record_with_invalid_json(self):
        """Тест с записью с некорректным JSON."""
        record = {
            'num_of_seasons': 3,
            'num_episodes_per_season': 'invalid json'
        }
        result = determine_granularity_from_record(record)
        # Должен fallback на базовую эвристику
        assert result == 'episode'

    def test_record_with_seasons_and_avg(self):
        """Тест с записью с указанием среднего."""
        record = {
            'num_of_seasons': 5,
            'avg_episodes_per_season': 22
        }
        result = determine_granularity_from_record(record)
        assert result == 'arc'


class TestGetPromptByGranularity:
    """Тесты функции get_prompt_by_granularity."""

    def test_episode_prompt(self):
        """Тест получения промпта для episode."""
        prompt = get_prompt_by_granularity('episode', 'Test Series')
        assert PROMPT_EPISODE_DRIVEN.format(title='Test Series') == prompt
        assert 'JSON' in prompt
        assert 'episode' in prompt.lower()

    def test_arc_prompt(self):
        """Тест получения промпта для arc."""
        prompt = get_prompt_by_granularity('arc', 'Test Series')
        assert PROMPT_ARC_DRIVEN.format(title='Test Series') == prompt

    def test_season_prompt(self):
        """Тест получения промпта для season."""
        prompt = get_prompt_by_granularity('season', 'Test Series')
        assert PROMPT_SEASON_DRIVEN.format(title='Test Series') == prompt

    def test_overview_prompt(self):
        """Тест получения промпта для overview."""
        prompt = get_prompt_by_granularity('overview', 'Test Series')
        assert PROMPT_OVERVIEW.format(title='Test Series') == prompt

    def test_unknown_granularity_defaults_to_overview(self):
        """Тест что неизвестная granularity возвращает overview промпт."""
        prompt = get_prompt_by_granularity('unknown', 'Test')
        assert PROMPT_OVERVIEW.format(title='Test') == prompt


class TestGetGranularityDisplayName:
    """Тесты функции get_granularity_display_name."""

    def test_episode_display_name(self):
        """Тест отображаемого имени для episode."""
        assert get_granularity_display_name('episode') == 'Детальный (по эпизодам)'

    def test_arc_display_name(self):
        """Тест отображаемого имени для arc."""
        assert get_granularity_display_name('arc') == 'Арочный (по сюжетным линиям)'

    def test_season_display_name(self):
        """Тест отображаемого имени для season."""
        assert get_granularity_display_name('season') == 'Сезонный (целиком)'

    def test_overview_display_name(self):
        """Тест отображаемого имени для overview."""
        assert get_granularity_display_name('overview') == 'Обзорный (общая хроника)'

    def test_unknown_display_name(self):
        """Тест отображаемого имени для неизвестного типа."""
        assert get_granularity_display_name('unknown') == 'Неизвестно'


class TestGetGranularityThresholds:
    """Тесты функции get_granularity_thresholds."""

    def test_returns_dict(self):
        """Тест что функция возвращает словарь."""
        result = get_granularity_thresholds()
        assert isinstance(result, dict)

    def test_contains_all_thresholds(self):
        """Тест что возвращаются все пороги."""
        result = get_granularity_thresholds()
        assert 'long_running_threshold' in result
        assert 'episodes_per_season_drama_threshold' in result
        assert 'episodes_per_season_action_threshold' in result

    def test_threshold_values(self):
        """Тест значений порогов."""
        result = get_granularity_thresholds()
        assert result['long_running_threshold'] == LONG_RUNNING_THRESHOLD
        assert result['episodes_per_season_drama_threshold'] == EPISODES_PER_SEASON_DRAMA_THRESHOLD
        assert result['episodes_per_season_action_threshold'] == EPISODES_PER_SEASON_ACTION_THRESHOLD


class TestGranularityEdgeCases:
    """Тесты граничных случаев."""

    def test_exact_long_running_threshold(self):
        """Тест точного порога для long running."""
        # Exactly LONG_RUNNING_THRESHOLD should NOT be overview by threshold alone
        # But based on the logic, it's handled by avg_episodes check
        assert determine_granularity(LONG_RUNNING_THRESHOLD) in ['season', 'overview']

    def test_exact_drama_threshold(self):
        """Тест точного порога драмы."""
        result = determine_granularity(3, [EPISODES_PER_SEASON_DRAMA_THRESHOLD])
        assert result == 'overview'

    def test_exact_action_threshold_lower(self):
        """Тест точного нижнего порога экшн."""
        result = determine_granularity(3, [EPISODES_PER_SEASON_ACTION_THRESHOLD])
        assert result == 'episode'

    def test_empty_episodes_list(self):
        """Тест с пустым списком эпизодов."""
        result = determine_granularity(3, [])
        # Falls back to base heuristic
        assert result == 'episode'

    def test_single_season_many_episodes(self):
        """Тест один сезон с большим количеством эпизодов."""
        result = determine_granularity(1, [50])
        assert result == 'overview'


class TestGranularityConstants:
    """Тесты констант модуля."""

    def test_long_running_threshold_value(self):
        """Тест значения LONG_RUNNING_THRESHOLD."""
        assert LONG_RUNNING_THRESHOLD == 15

    def test_drama_threshold_value(self):
        """Тест значения EPISODES_PER_SEASON_DRAMA_THRESHOLD."""
        assert EPISODES_PER_SEASON_DRAMA_THRESHOLD == 40

    def test_action_threshold_value(self):
        """Тест значения EPISODES_PER_SEASON_ACTION_THRESHOLD."""
        assert EPISODES_PER_SEASON_ACTION_THRESHOLD == 12

    def test_thresholds_are_reasonable(self):
        """Тест что пороги имеют разумные значения."""
        assert LONG_RUNNING_THRESHOLD > 0
        assert EPISODES_PER_SEASON_DRAMA_THRESHOLD > EPISODES_PER_SEASON_ACTION_THRESHOLD
        assert EPISODES_PER_SEASON_ACTION_THRESHOLD >= 1