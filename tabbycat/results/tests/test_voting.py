import logging

from django.test import TestCase

from adjallocation.models import DebateAdjudicator
from draw.models import Debate, DebateTeam
from participants.models import Adjudicator, Institution, Speaker, Team
from results.models import BallotSubmission, SpeakerScore, SpeakerScoreByAdj, TeamScore
from results.result import VotingDebateResult    # absolute import to keep logger's name consistent
from tournaments.models import Round, Tournament
from utils.tests import suppress_logs
from venues.models import Venue


class TestVotingDebateResult(TestCase):

    testdata = dict()
    testdata[1] = {
        # data that gets written to the form
        'declared_winners': ['neg', 'neg', 'neg'],
        'scores': [[[75.0, 76.0, 74.0, 38.0], [76.0, 73.0, 75.0, 37.5]],
                   [[74.0, 75.0, 76.0, 37.0], [77.0, 74.0, 74.0, 38.0]],
                   [[75.0, 75.0, 75.0, 37.5], [76.0, 78.0, 77.0, 37.0]]],
        # calculated fields that are the same in all scoresheet types
        'everyone_margins': [-1.66666666666667, 1.66666666666667],
        'everyone_scores': [[74.66666666666667, 75.33333333333333, 75.0, 37.5],
                            [76.33333333333333, 75.0, 75.33333333333333, 37.5]],
        'everyone_totals': [262.5, 264.16666666666667],
        'num_adjs': 3,
        'num_speakers_per_team': 3,
        'totals_by_adj': [[263, 261.5], [262, 263], [262.5, 268]],
        # calculated fields that depend on the scoresheet type
        # 'high-required': {
            'majority_adjs': [1, 2],
            'majority_margins': [-3.25, 3.25],
            'majority_scores': [[74.5, 75, 75.5, 37.25], [76.5, 76, 75.5, 37.5]],
            'majority_totals': [262.25, 265.5],
            'num_adjs_for_team': [1, 2],
            'winner': 'neg',
            'winner_by_adj': ['aff', 'neg', 'neg'],
        # },
        # 'low-allowed': {
        #     'majority_adjs': [0, 1, 2],
        #     'majority_margins': [-1.66666666666667, 1.66666666666667],
        #     'majority_scores': [[74.66666666666667, 75.33333333333333, 75.0, 37.5],
        #                         [76.33333333333333, 75.0, 75.33333333333333, 37.5]],
        #     'majority_totals': [262.5, 264.16666666666667],
        #     'num_adjs_for_team': [0, 3],
        #     'winner': 'neg',
        #     'winner_by_adj': ['neg', 'neg', 'neg'],
        # }
    }
    testdata[2] = {
        'declared_winners': ['aff', 'neg', 'neg'],
        'everyone_margins': [-6.166666666666667, 6.166666666666667],
        'everyone_scores': [[75.0, 75.33333333333333, 75.33333333333333, 36.166666666666667],
                            [77.0, 77.33333333333333, 76.0, 37.666666666666667]],
        'everyone_totals': [261.8333333333333, 268.0],
        'majority_adjs': [0, 1, 2],
        'majority_margins': [-6.166666666666667, 6.166666666666667],
        'majority_scores': [[75.0, 75.33333333333333, 75.33333333333333, 36.166666666666667],
                            [77.0, 77.33333333333333, 76.0, 37.666666666666667]],
        'majority_totals': [261.8333333333333, 268.0],
        'num_adjs': 3,
        'num_adjs_for_team': [0, 3],
        'num_speakers_per_team': 3,
        'scores': [[[73.0, 76.0, 79.0, 37.5], [77.0, 77.0, 78.0, 39.0]],
                   [[79.0, 80.0, 70.0, 36.0], [78.0, 79.0, 73.0, 37.0]],
                   [[73.0, 70.0, 77.0, 35.0], [76.0, 76.0, 77.0, 37.0]]],
        'totals_by_adj': [[265.5, 271.0], [265.0, 267.0], [255.0, 266.0]],
        'winner': 'neg',
        'winner_by_adj': ['neg', 'neg', 'neg'],
    }
    testdata[3] = {
        'declared_winners': ['neg', 'aff', 'neg'],
        'everyone_margins': [4.33333333333333, -4.33333333333333],
        'everyone_scores': [[74.66666666666667, 74.33333333333333, 77.66666666666667, 39.166666666666667],
                            [74.33333333333333, 73.66666666666667, 75.0, 38.5]],
        'everyone_totals': [265.83333333333333, 261.5],
        'majority_adjs': [1, 2],
        'majority_margins': [11.75, -11.75],
        'majority_scores': [[75.5, 76.5, 77.5, 38.75], [71.5, 71.5, 75.0, 38.5]],
        'majority_totals': [268.25, 256.5],
        'num_adjs': 3,
        'num_adjs_for_team': [2, 1],
        'num_speakers_per_team': 3,
        'scores': [[[73.0, 70.0, 78.0, 40.0], [80.0, 78.0, 75.0, 38.5]],
                   [[79.0, 75.0, 75.0, 39.5], [73.0, 73.0, 73.0, 40.0]],
                   [[72.0, 78.0, 80.0, 38.0], [70.0, 70.0, 77.0, 37.0]]],
        'totals_by_adj': [[261.0, 271.5], [268.5, 259.0], [268.0, 254.0]],
        'winner': 'aff',
        'winner_by_adj': ['neg', 'aff', 'aff'],
    }
    testdata[4] = {
        'declared_winners': ['aff'],
        'everyone_margins': [-0.5, 0.5],
        'everyone_scores': [[74.0, 76.0, 37.5], [74.0, 77.0, 37.0]],
        'everyone_totals': [187.5, 188.0],
        'majority_adjs': [0],
        'majority_margins': [-0.5, 0.5],
        'majority_scores': [[74.0, 76.0, 37.5], [74.0, 77.0, 37.0]],
        'majority_totals': [187.5, 188.0],
        'num_adjs': 1,
        'num_adjs_for_team': [0, 1],
        'num_speakers_per_team': 2,
        'scores': [[[74.0, 76.0, 37.5], [74.0, 77.0, 37.0]]],
        'totals_by_adj': [[187.5, 188.0]],
        'winner': 'neg',
        'winner_by_adj': ['neg'],
    }
    testdata[5] = { # even panel, chair gets casting vote, note this is a low-point win
        'declared_winners': ['neg', 'aff'],
        'everyone_margins': [4.25, -4.25],
        'everyone_scores': [[80.0, 76.5, 36.5], [76.0, 73.5, 39.25]],
        'everyone_totals': [193.0, 188.75],
        'majority_adjs': [0],
        'majority_margins': [-4.5, 4.5],
        'majority_scores': [[80.0, 74.0, 35.5], [79.0, 76.0, 39.0]],
        'majority_totals': [189.5, 194.0],
        'num_adjs': 2,
        'num_adjs_for_team': [1, 1],
        'num_speakers_per_team': 2,
        'scores': [[[80.0, 74.0, 35.5], [79.0, 76.0, 39.0]],
                   [[80.0, 79.0, 37.5], [73.0, 71.0, 39.5]]],
        'totals_by_adj': [[189.5, 194.0], [196.5, 183.5]],
        'winner': 'neg',
        'winner_by_adj': ['neg', 'aff'],
    }

    SIDES = ['aff', 'neg']
    SIDE_KEY_MAP_REVERSE = {
        'aff': DebateTeam.POSITION_AFFIRMATIVE,
        'neg': DebateTeam.POSITION_NEGATIVE,
    }

    def setUp(self):
        self.t = Tournament.objects.create(slug="resulttest", name="ResultTest")
        self.teams = []
        for i in range(2):
            inst = Institution.objects.create(code="Inst{:d}".format(i), name="Institution {:d}".format(i))
            team = Team.objects.create(tournament=self.t, institution=inst, reference="Team {:d}".format(i), use_institution_prefix=False)
            self.teams.append(team)
            for j in range(3):
                Speaker.objects.create(team=team, name="Speaker {:d}-{:d}".format(i, j))

        venue = Venue.objects.create(name="Venue", priority=10)

        rd = Round.objects.create(tournament=self.t, seq=1, abbreviation="R1")
        self.debate = Debate.objects.create(round=rd, venue=venue)

        sides = [DebateTeam.POSITION_AFFIRMATIVE, DebateTeam.POSITION_NEGATIVE]
        for team, side in zip(Team.objects.all(), sides):
            DebateTeam.objects.create(debate=self.debate, team=team, position=side)

        inst = Institution.objects.create(code="Adjs", name="Adjudicators")
        self.adjs = [Adjudicator.objects.create(tournament=self.t, institution=inst,
                name="Adjudicator {:d}".format(i), test_score=5) for i in range(3)]

    def tearDown(self):
        DebateTeam.objects.all().delete()
        Institution.objects.all().delete()
        self.t.delete()

    def set_tournament_preference(self, section, name, value):
        self.t.preferences[section + '__' + name] = value
        if name in self.t._prefs:    # clear model-level cache
            del self.t._prefs[name]

    def with_preference(section, name, value):  # flake8: noqa
        """Decorator. Sets a tournament preference before it begins the wrapped
        function. The main purpose of this decorator is to be used with other
        decorators, otherwise it could obviously just be achieved with a single
        line at the beginning of the function. This decorator should normally be
        placed first in the decorator chain, so that it is the outermost
        wrapper."""
        def wrap(test_fn):
            def wrapped(self, *args, **kwargs):
                self.set_tournament_preference(section, name, value)
                test_fn(self, *args, **kwargs)
            return wrapped
        return wrap

    def on_scoresheet_types(*scoresheet_types):
        """Decorator. Tests on all scoresheet types listed in the argument."""
        def wrap(test_fn):
            def wrapped(self, *args, **kwargs):
                for scoresheet_type in scoresheet_types:
                    with self.subTest(scoresheet_type=scoresheet_type):
                        self.set_tournament_preference('scoring', 'scoresheet_type', scoresheet_type)
                        test_fn(self, *args, **kwargs)
            return wrapped
        return wrap

    on_all_scoresheet_types = on_scoresheet_types('high-required', 'low-allowed', 'tied-allowed', 'result-only')

    def on_all_datasets(test_fn):  # flake8: noqa
        """Decorator. Tests on all datasets in self.testdata. Tests should be
        written to take three arguments: self, result and testdata. `result` is
        a VotingDebateResult object. `testdata` is a value of
        BaseTestResult.testdata. This decorator then sets up the
        VotingDebateResult and runs the test once for each test dataset in
        BaseTestResult.testdata."""
        def wrap(self):
            for key, testdata in self.testdata.items():
                with self.subTest(testdata=key):
                    self.save_complete_result(testdata)
                    result = self.get_result()
                    test_fn(self, result, testdata)
        return wrap

    def get_result(self):
        ballotsub = BallotSubmission.objects.get(debate=self.debate, confirmed=True)
        return VotingDebateResult(ballotsub)

    def save_blank_result(self, nadjs=3, nspeakers=3):

        self.set_tournament_preference('debate_rules', 'substantive_speakers', nspeakers)

        # set debate adjudicators (depends on how many adjs there are, so can't do in setUp())
        self.debate.adjudicators.chair = self.adjs[0]
        self.debate.adjudicators.panellists = self.adjs[1:nadjs]
        with suppress_logs('adjallocation.allocation', logging.INFO):
            self.debate.adjudicators.save()

        # unconfirm existing ballots
        self.debate.ballotsubmission_set.update(confirmed=False)

        ballotsub = BallotSubmission.objects.create(debate=self.debate, confirmed=True,
                submitter_type=BallotSubmission.SUBMITTER_TABROOM)

        return VotingDebateResult(ballotsub)

    def save_complete_result(self, testdata, post_create=None):

        nspeakers = testdata['num_speakers_per_team']

        result = self.save_blank_result(nadjs=testdata['num_adjs'], nspeakers=nspeakers)
        if post_create:
            post_create(result)

        for side, team in zip(self.SIDES, self.teams):
            speakers = team.speaker_set.all()[0:nspeakers]
            for pos, speaker in enumerate(speakers, start=1):
                result.set_speaker(side, pos, speaker)
            result.set_speaker(side, nspeakers+1, speakers[0])
            # ghost fields should be False by default

        if result.requires_scores:
            for adj, sheet in zip(self.adjs, testdata['scores']):
                for side, teamscores in zip(self.SIDES, sheet):
                    for pos, score in enumerate(teamscores, start=1):
                        result.set_score(adj, side, pos, score)

        if result.requires_declared_winners:
            for adj, declared_winner in zip(self.adjs, testdata['declared_winners']):
                result.set_declared_winner(adj, declared_winner)

        with suppress_logs('results.result', logging.WARNING):
            result.save()

    # ==========================================================================
    # Normal operation
    # ==========================================================================

    # @on_all_scoresheet_types
    @on_all_datasets
    def test_save(self, result, testdata):
        # Run self.save_complete_result and check completeness
        self.assertTrue(result.is_complete)

    # @on_scoresheet_types('high-required', 'low-allowed', 'tied-allowed')
    @on_all_datasets
    def test_totals_by_adj(self, result, testdata):
        for adj, totals in zip(self.adjs, testdata['totals_by_adj']):
            for side, total in zip(self.SIDES, totals):
                self.assertEqual(total, result.scoresheets[adj].get_total(side))

    # @on_scoresheet_types('high-required', 'low-allowed', 'tied-allowed')
    @on_all_datasets
    def test_majority_adjudicators(self, result, testdata):
        majority = [self.adjs[i] for i in testdata['majority_adjs']]
        with suppress_logs('results.result', logging.WARNING):
            self.assertCountEqual(majority, result.majority_adjudicators())

    # @on_scoresheet_types('high-required', 'low-allowed', 'tied-allowed')
    @on_all_datasets
    def test_individual_scores(self, result, testdata):
        for adj, sheet in zip(self.adjs, testdata['scores']):
            for side, scores in zip(self.SIDES, sheet):
                for pos, score in enumerate(scores, start=1):
                    score_in_db = SpeakerScoreByAdj.objects.get(
                        ballot_submission__debate=self.debate,
                        ballot_submission__confirmed=True,
                        debate_team__position=self.SIDE_KEY_MAP_REVERSE[side],
                        debate_adjudicator__adjudicator=adj,
                        position=pos).score
                    self.assertEqual(score, score_in_db)
                    self.assertEqual(score, result.get_score(adj, side, pos))

    @on_all_datasets
    def test_winner_by_adj(self, result, testdata):
        for adj, winner in zip(self.adjs, testdata['winner_by_adj']):
            self.assertEqual(result.scoresheets[adj].winner(), winner)

    # --------------------------------------------------------------------------
    # Speaker scores
    # --------------------------------------------------------------------------

    def _get_speakerscore_in_db(self, side, pos):
        return SpeakerScore.objects.get(
            ballot_submission__debate=self.debate,
            ballot_submission__confirmed=True,
            debate_team__position=self.SIDE_KEY_MAP_REVERSE[side],
            position=pos
        )

    @with_preference('scoring', 'margin_includes_dissenters', False)
    @on_all_datasets
    def test_speaker_scores_majority(self, result, testdata):
        for side, totals in zip(self.SIDES, testdata['majority_scores']):
            for pos, score in enumerate(totals, start=1):
                with suppress_logs('results.result', logging.WARNING):
                    self.assertAlmostEqual(score, self._get_speakerscore_in_db(side, pos).score)
                    self.assertAlmostEqual(score, result.get_speaker_score(side, pos))

    @with_preference('scoring', 'margin_includes_dissenters', True)
    @on_all_datasets
    def test_speaker_scores_everyone(self, result, testdata):
        for side, totals in zip(self.SIDES, testdata['everyone_scores']):
            for pos, score in enumerate(totals, start=1):
                with suppress_logs('results.result', logging.WARNING):
                    self.assertAlmostEqual(score, self._get_speakerscore_in_db(side, pos).score)
                    self.assertAlmostEqual(score, result.get_speaker_score(side, pos))

    # --------------------------------------------------------------------------
    # Team scores
    # --------------------------------------------------------------------------

    def _get_teamscore_in_db(self, side):
        return TeamScore.objects.get(
            ballot_submission__debate=self.debate,
            ballot_submission__confirmed=True,
            debate_team__position=self.SIDE_KEY_MAP_REVERSE[side]
        )

    @on_all_datasets
    def test_teamscorefield_points(self, result, testdata):
        for side in self.SIDES:
            points = 1 if side == testdata['winner'] else 0
            with suppress_logs('results.result', logging.WARNING):
                self.assertEqual(points, self._get_teamscore_in_db(side).points)
                self.assertEqual(points, result.teamscorefield_points(side))

    @on_all_datasets
    def test_teamscorefield_win(self, result, testdata):
        for side in self.SIDES:
            win = side == testdata['winner']
            with suppress_logs('results.result', logging.WARNING):
                self.assertEqual(win, self._get_teamscore_in_db(side).win)
                self.assertEqual(win, result.teamscorefield_win(side))

    @with_preference('scoring', 'margin_includes_dissenters', False)
    @on_all_datasets
    def test_teamscorefield_score_majority(self, result, testdata):
        for side, total in zip(self.SIDES, testdata['majority_totals']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertAlmostEqual(total, self._get_teamscore_in_db(side).score)
                self.assertAlmostEqual(total, result.teamscorefield_score(side))

    @with_preference('scoring', 'margin_includes_dissenters', False)
    @on_all_datasets
    def test_teamscorefield_margin_majority(self, result, testdata):
        for side, margin in zip(self.SIDES, testdata['majority_margins']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertAlmostEqual(margin, self._get_teamscore_in_db(side).margin)
                self.assertAlmostEqual(margin, result.teamscorefield_margin(side))

    @with_preference('scoring', 'margin_includes_dissenters', True)
    @on_all_datasets
    def test_teamscorefield_score_everyone(self, result, testdata):
        for side, total in zip(self.SIDES, testdata['everyone_totals']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertAlmostEqual(total, self._get_teamscore_in_db(side).score)
                self.assertAlmostEqual(total, result.teamscorefield_score(side))

    @with_preference('scoring', 'margin_includes_dissenters', True)
    @on_all_datasets
    def test_teamscorefield_margin_everyone(self, result, testdata):
        for side, margin in zip(self.SIDES, testdata['everyone_margins']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertAlmostEqual(margin, self._get_teamscore_in_db(side).margin)
                self.assertAlmostEqual(margin, result.teamscorefield_margin(side))

    @on_all_datasets
    def test_teamscorefield_votes_given(self, result, testdata):
        for side, votes in zip(self.SIDES, testdata['num_adjs_for_team']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertEqual(votes, self._get_teamscore_in_db(side).votes_given)
                self.assertEqual(votes, result.teamscorefield_votes_given(side))

    @on_all_datasets
    def test_teamscorefield_votes_possible(self, result, testdata):
        nadjs = testdata['num_adjs']
        for side in self.SIDES:
            self.assertEqual(nadjs, self._get_teamscore_in_db(side).votes_possible)
            self.assertEqual(nadjs, result.teamscorefield_votes_possible(side))

    # ==========================================================================
    # Unknown sides
    # ==========================================================================

    def _unset_sides(self):
        for dt in self.debate.debateteam_set.all():
            dt.position = DebateTeam.POSITION_UNALLOCATED
            dt.save()

    def test_save_speaker_with_unknown_sides(self):
        self._unset_sides()
        result = self.save_blank_result()
        self.assertRaises(TypeError, result.set_speaker, 'aff', 1, None)

    def test_unknown_speaker(self):
        self.save_complete_result(self.testdata[1])
        result = self.get_result()
        neg_speaker = self.teams[1].speaker_set.first()
        with self.assertLogs('results.result', level=logging.ERROR) as cm:
            result.set_speaker('aff', 1, neg_speaker)

    def test_initially_unknown_sides(self):
        self.set_tournament_preference('scoring', 'margin_includes_dissenters', False)
        self._unset_sides()
        testdata = self.testdata[1]
        self.save_complete_result(testdata,
                post_create=lambda result: result.set_sides(*self.teams))
        result = self.get_result()

        # Just check a couple of fields
        for side, margin in zip(self.SIDES, testdata['majority_margins']):
            with suppress_logs('results.result', logging.WARNING):
                self.assertEqual(self._get_teamscore_in_db(side).win, side == testdata['winner'])
                self.assertEqual(result.teamscorefield_win(side), side == testdata['winner'])
                self.assertAlmostEqual(self._get_teamscore_in_db(side).margin, margin)
                self.assertAlmostEqual(result.teamscorefield_margin(side), margin)

    # ==========================================================================
    # Not complete
    # ==========================================================================

    def incomplete_test(test_fn):  # flake8: noqa
        def wrap(self):
            testdata = self.testdata[1]
            if not BallotSubmission.objects.filter(debate=self.debate, confirmed=True).exists():
                self.save_complete_result(testdata)
            result = self.get_result()
            test_fn(self, result)
            self.assertFalse(result.is_complete)
        return wrap

    @incomplete_test
    def test_unfilled_debateteam(self, result):
        result.debateteams["aff"] = None

    @incomplete_test
    def test_unfilled_speaker(self, result):
        result.speakers["neg"][1] = None

    @incomplete_test
    def test_unfilled_scoresheet_score(self, result):
        result.scoresheets[self.adjs[0]].scores["aff"][1] = None

    # ==========================================================================
    # Not properly loaded
    # ==========================================================================

    def bad_load_assertion_test(test_fn):  # flake8: noqa
        def wrap(self):
            testdata = self.testdata[1]
            if not BallotSubmission.objects.filter(debate=self.debate, confirmed=True).exists():
                self.save_complete_result(testdata)
            result = self.get_result()
            test_fn(self, result)
            self.assertRaises(AssertionError, result.assert_loaded)
        return wrap

    @bad_load_assertion_test
    def test_extraneous_debateteam(self, result):
        result.debateteams["test"] = None

    @bad_load_assertion_test
    def test_extraneous_team_in_speakers(self, result):
        result.speakers["test"] = None

    @bad_load_assertion_test
    def test_extraneous_team_in_ghosts(self, result):
        result.ghosts["test"] = True

    @bad_load_assertion_test
    def test_extraneous_speaker(self, result):
        result.speakers["aff"][5] = None

    @bad_load_assertion_test
    def test_extraneous_ghost(self, result):
        result.ghosts["aff"][5] = None

    @bad_load_assertion_test
    def test_extraneous_scoresheet(self, result):
        result.scoresheets["not-an-adj"] = None
