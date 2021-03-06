#!/usr/bin/env python3

import logging
import os
import sys
import schematics
import basemodels
import unittest
import httpretty
import json

CALLBACK_URL = "http://google.com/webback"
FAKE_URL = "http://google.com/fake"
IMAGE_LABEL_BINARY = "image_label_binary"

REP_ORACLE = "0x61F9F0B31eacB420553da8BCC59DC617279731Ac"
REC_ORACLE = "0xD979105297fB0eee83F7433fC09279cb5B94fFC6"
FAKE_ORACLE = "0x1413862c2b7054cdbfdc181b83962cb0fc11fd92"


def a_manifest(number_of_tasks=100,
               bid_amount=1.0,
               oracle_stake=0.05,
               expiration_date=0,
               minimum_trust=.1,
               request_type=IMAGE_LABEL_BINARY,
               request_config=None,
               job_mode='batch',
               multi_challenge_manifests=None) -> basemodels.Manifest:
    internal_config = {'exchange': {'a': 1, 'b': 'c'}}
    model = {
        'requester_restricted_answer_set': {
            '0': {
                'en': 'English Answer 1'
            },
            '1': {
                'en': 'English Answer 2',
                'answer_example_uri': 'https://hcaptcha.com/example_answer2.jpg'
            }
        },
        'job_mode': job_mode,
        'request_type': request_type,
        'internal_config': internal_config,
        'multi_challenge_manifests': multi_challenge_manifests,
        'unsafe_content': False,
        'task_bid_price': bid_amount,
        'oracle_stake': oracle_stake,
        'expiration_date': expiration_date,
        'minimum_trust_server': minimum_trust,
        'minimum_trust_client': minimum_trust,
        'requester_accuracy_target': minimum_trust,
        'recording_oracle_addr': REC_ORACLE,
        'reputation_oracle_addr': REP_ORACLE,
        'reputation_agent_addr': REP_ORACLE,
        'instant_result_delivery_webhook': CALLBACK_URL,
        'requester_question': {
            "en": "How much money are we to make"
        },
        'requester_question_example': FAKE_URL,
        'job_total_tasks': number_of_tasks,
        'taskdata_uri': FAKE_URL
    }

    if request_config:
        model.update({'request_config': request_config})

    manifest = basemodels.Manifest(model)
    manifest.validate()

    return manifest


def a_nested_manifest(request_type=IMAGE_LABEL_BINARY, minimum_trust=.1,
                      request_config=None) -> basemodels.Manifest:
    model = {
        'requester_restricted_answer_set': {
            '0': {
                'en': 'English Answer 1'
            },
            '1': {
                'en': 'English Answer 2',
                'answer_example_uri': 'https://hcaptcha.com/example_answer2.jpg'
            }
        },
        'request_type': request_type,
        'requester_accuracy_target': minimum_trust,
        'requester_question': {
            "en": "How much money are we to make"
        },
        'requester_question_example': FAKE_URL,
    }

    if request_config:
        model.update({'request_config': request_config})

    manifest = basemodels.NestedManifest(model)
    manifest.validate()

    return manifest


class ManifestTest(unittest.TestCase):
    """Manifest specific tests, validating that models work the way we want"""

    def test_basic_construction(self):
        """Tests that manifest can validate the test manifest properly."""
        a_manifest()

    def test_can_serialize(self):
        """ validate that we can dump this to json in downstream services """
        j = json.dumps(a_manifest().to_primitive())

    def test_can_fail_toconstruct(self):
        """Tests that the manifest raises an Error when called with falsy parameters."""
        a_manifest(-1)
        self.assertRaises(schematics.exceptions.DataError, a_manifest, "invalid amount")

    def test_can_fail_toconstruct2(self):
        """Tests that validated fields can't be broken without an exception."""
        mani = a_manifest()
        mani.taskdata_uri = 'test'
        self.assertRaises(schematics.exceptions.DataError, mani.validate)

    def test_can_make_request_config_job(self):
        """Test that jobs with valid request_config parameter work"""
        manifest = a_manifest(
            request_type='image_label_area_select', request_config={'shape_type': 'point'})

    def test_can_make_nested_request_config_job_single_nest(self):
        """Test that jobs with valid nested request_config parameter work"""
        nested_manifest = a_nested_manifest(
            request_type='image_label_area_select', request_config={'shape_type': 'point'})

        manifest = a_manifest(
            request_type='multi_challenge', multi_challenge_manifests=[nested_manifest])

    def test_can_make_nested_request_config_job_multiple_nest(self):
        """Test that jobs with multiple valid nested request_config parameters work"""
        nested_manifest = a_nested_manifest(
            request_type='image_label_area_select', request_config={'shape_type': 'point'})

        nested_manifest_2 = a_nested_manifest(
            request_type='image_label_area_select', request_config={'shape_type': 'point'})

        manifest = a_manifest(
            request_type='multi_challenge',
            multi_challenge_manifests=[nested_manifest, nested_manifest_2])

    def test_can_bad_request_config(self):
        """Test that an invalid shape_type in request_config will fail"""
        manifest = a_manifest()
        manifest.request_type = 'image_label_area_select'
        manifest.request_config = {'shape_type': 'not-a-real-option'}
        self.assertRaises(schematics.exceptions.DataError, manifest.validate)

    def test_gets_default_restrictedanswerset(self):
        """Make sure that the image_label_area_select jobs get a default RAS"""
        model = {
            'job_mode': 'batch',
            'request_type': 'image_label_area_select',
            'unsafe_content': False,
            'task_bid_price': 1,
            'oracle_stake': 0.1,
            'expiration_date': 0,
            'minimum_trust_server': .1,
            'minimum_trust_client': .1,
            'requester_accuracy_target': .1,
            'recording_oracle_addr': REC_ORACLE,
            'reputation_oracle_addr': REP_ORACLE,
            'reputation_agent_addr': REP_ORACLE,
            'instant_result_delivery_webhook': CALLBACK_URL,
            'requester_question': {
                "en": "How much money are we to make"
            },
            'requester_question_example': FAKE_URL,
            'job_total_tasks': 5,
            'taskdata_uri': FAKE_URL
        }
        manifest = basemodels.Manifest(model)

        manifest.validate()
        self.assertGreater(len(manifest['requester_restricted_answer_set'].keys()), 0)

    def test_confcalc_configuration_id(self):
        """ Test that key is in manifest """
        manifest = a_manifest()
        manifest.confcalc_configuration_id = 'test_conf_id'
        manifest.validate()

        self.assertTrue("confcalc_configuration_id" in manifest.to_primitive())

    def test_url_or_list_for_example(self):
        """ validates that we can supply a list or a url to example key """
        model = a_manifest()

        model.requester_question_example = "https://test.com"
        self.assertTrue(model.validate() is None)
        self.assertIsInstance(model.to_primitive()['requester_question_example'], str)

        model.requester_question_example = ["https://test.com"]
        self.assertTrue(model.validate() is None)
        self.assertIsInstance(model.to_primitive()['requester_question_example'], list)

        model.requester_question_example = "non-url"
        self.assertRaises(schematics.exceptions.DataError, model.validate)
        model.requester_question_example = ["non-url"]
        self.assertRaises(schematics.exceptions.DataError, model.validate)

        # we now allow lists in non-ilb types
        model.request_type = "image_label_area_select"
        self.assertTrue(model.validate)

    def test_restricted_audience(self):
        """ Test that restricted audience is in the Manifest """
        manifest = a_manifest()
        manifest.restricted_audience = {
            "lang": [{
                "en-us": {
                    "score": 0.9
                }
            }],
            "confidence": [{
                "minimum_client_confidence": {
                    "score": 0.9
                }
            }],
            "min_difficulty": 2,
        }
        manifest.validate()
        self.assertTrue("restricted_audience" in manifest.to_primitive())
        self.assertTrue("minimum_client_confidence" in manifest.to_primitive()
                        ["restricted_audience"]["confidence"][0])
        self.assertEqual(
            0.9,
            manifest.to_primitive()["restricted_audience"]["confidence"][0]
            ["minimum_client_confidence"]["score"])
        self.assertTrue("en-us" in manifest.to_primitive()["restricted_audience"]["lang"][0])
        self.assertEqual(
            0.9,
            manifest.to_primitive()["restricted_audience"]["lang"][0]["en-us"]["score"])
        self.assertEqual(2, manifest.to_primitive()["restricted_audience"]["min_difficulty"])

    def test_realistic_multi_challenge_example(self):
        """ validates a realistic multi_challenge manifest """
        obj = {
            'job_mode': 'batch',
            'request_type': 'image_label_area_select',
            'unsafe_content': False,
            'task_bid_price': 1,
            'oracle_stake': 0.1,
            'expiration_date': 0,
            'minimum_trust_server': .1,
            'minimum_trust_client': .1,
            'requester_accuracy_target': .1,
            'job_total_tasks': 1000,
            'recording_oracle_addr': REC_ORACLE,
            'reputation_oracle_addr': REP_ORACLE,
            'reputation_agent_addr': REP_ORACLE,
            "job_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
            "request_type": "multi_challenge",
            "requester_question": {
                "en": "Please draw a bow around the text shown, select the best corresponding labels, and enter the word depicted by the image."
            },
            "multi_challenge_manifests": [{
                "request_type": "image_label_area_select",
                "job_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
                "requester_question": {
                    "en": "Please draw a bow around the text shown."
                },
                "request_config": {
                    "shape_type": "polygon",
                    "min_points": 1,
                    "max_points": 4,
                    "min_shapes_per_image": 1,
                    "max_shapes_per_image": 4
                }
            },
                                          {
                                              "request_type": "image_label_multiple_choice",
                                              "job_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
                                              "requester_question": {
                                                  "en": "Select the corresponding label."
                                              },
                                              "requester_restricted_answer_set": {
                                                  "print": {
                                                      "en": "Print"
                                                  },
                                                  "hand-writing": {
                                                      "en": "Hand Writing"
                                                  }
                                              },
                                              "request_config": {
                                                  "multiple_choice_max_choices": 1
                                              }
                                          },
                                          {
                                              "request_type": "image_label_multiple_choice",
                                              "job_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
                                              "requester_question": {
                                                  "en": "Select the corresponding labels."
                                              },
                                              "requester_restricted_answer_set": {
                                                  "top-bottom": {
                                                      "en": "Top to Bottom"
                                                  },
                                                  "bottom-top": {
                                                      "en": "Bottom to Top"
                                                  },
                                                  "left-right": {
                                                      "en": "Left to Right"
                                                  },
                                                  "right-left": {
                                                      "en": "Right to Left"
                                                  }
                                              },
                                              "request_config": {
                                                  "multiple_choice_max_choices": 1
                                              }
                                          },
                                          {
                                              "request_type": "image_label_text",
                                              "job_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
                                              "requester_question": {
                                                  "en": "Please enter the word in the image."
                                              }
                                          }],
            "taskdata": [{
                "datapoint_hash": "sha1:5daf66c6031df7f8913bfa0b52e53e3bcd42aab3",
                "datapoint_uri": "http://test.com/task.jpg",
                "task_key": "2279daef-d10a-4b0f-85d1-0ccbf7c8906b"
            }]
        }

        model = basemodels.Manifest(obj)
        # print(model.to_primitive())
        self.assertTrue(model.validate() is None)

    def test_webhook(self):
        """ Test that webhook is correct """
        webhook = {
            "webhook_id": "c26c2e6a-41ab-4218-b39e-6314b760c45c",
            "job_completed": ["http://servicename:4000/api/webhook"]
        }

        webhook_model = basemodels.Webhook(webhook)
        webhook_model.validate()
        self.assertTrue("webhook_id" in webhook_model.to_primitive())

        model = a_manifest()
        model.webhook = webhook
        model.validate()
        self.assertTrue("webhook" in model.to_primitive())


class ViaTest(unittest.TestCase):
    def test_via_legacy_case(self):
        """ tests case with inner class_attributes """
        content = {
            "datapoints": [{
                "task_uri": "https://mydomain.com/image.jpg",
                "metadata": {
                    "filename": "image.jpg"
                },
                "class_attributes": {
                    "0": {
                        "class_attributes": {
                            "dog": False,
                            "cat": False
                        }
                    }
                },
                "regions": [{
                    "region_attributes": {
                        "region_key": "region_value"
                    },
                    "shape_attributes": {
                        "coords": [1, 2, 3, 4, 5, 6, 7, 8.],
                        "name": "shape_type"
                    }
                }],
            }]
        }

        parsed = basemodels.ViaDataManifest().dump(content)
        self.assertEqual(len(parsed['datapoints']), 1)
        self.assertEqual(parsed['version'], 1)

    def test_via_v1_case(self):
        """ tests case where we dont use the inner class_attributes """
        content = {
            "datapoints": [{
                "task_uri": "https://mydomain.com/image.jpg",
                "metadata": {
                    "filename": "image.jpg"
                },
                "class_attributes": {
                    "dog": False,
                    "cat": False
                },
                "regions": [{
                    "region_attributes": {
                        "region_key": "region_value"
                    },
                    "shape_attributes": {
                        "coords": [1, 2, 3, 4, 5, 6, 7, 8.],
                        "name": "shape_type"
                    }
                }],
            }]
        }

        parsed = basemodels.ViaDataManifest().dump(content)
        self.assertEqual(len(parsed['datapoints']), 1)
        self.assertEqual(parsed['version'], 1)
        self.assertIn('dog', parsed['datapoints'][0]['class_attributes'])


@httpretty.activate
class TestValidateManifestUris(unittest.TestCase):
    def register_http_response(self, uri="https://uri.com", manifest=None, body=None):
        httpretty.register_uri(httpretty.GET, uri, body=json.dumps(body))

    def validate_groundtruth_response(self, request_type, body):
        uri = "https://uri.com"
        manifest = {"groundtruth_uri": uri, "request_type": request_type}

        self.register_http_response(uri, manifest, body)

        basemodels.validate_manifest_uris(manifest)

    def test_no_uris(self):
        """ should not raise if there are no uris to validate """
        manifest = {}
        basemodels.validate_manifest_uris(manifest)

    def test_groundtruth_uri_ilb_valid(self):
        body = {
            "https://domain.com/123/file1.jpeg": ["false", "false", "false"],
            "https://domain.com/456/file2.jpeg": ["false", "true", "false"],
        }

        self.validate_groundtruth_response("image_label_binary", body)

    def test_groundtruth_uri_ilb_invalid(self):
        body = {"not_uri": ["false", "false", True]}

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_binary", body)

    def test_groundtruth_uri_ilb_invalid_format(self):
        """ should raise if groundtruth_uri contains array instead of object """
        body = [{"key": "value"}]

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_binary", body)

    def test_groundtruth_uri_ilmc_valid(self):
        body = {
            "https://domain.com/file1.jpeg": [["cat"], ["cat"], ["cat"]],
            "https://domain.com/file2.jpeg": [["dog"], ["dog"], ["dog"]]
        }

        self.validate_groundtruth_response("image_label_multiple_choice", body)

    def test_groundtruth_uri_ilmc_invalid_key(self):
        body = {"not_uri": [["cat"], ["cat"], ["cat"]]}

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_multiple_choice", body)

    def test_groundtruth_uri_ilmc_invalid_value(self):
        body = {
            "https://domain.com/file1.jpeg": [True, False],
        }

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_multiple_choice", body)

    def test_groundtruth_uri_ilas_valid(self):
        body = {
            "https://domain.com/file1.jpeg": [[{
                "entity_name": 0,
                "entity_type": "gate",
                "entity_coords": [275, 184, 454, 183, 453, 366, 266, 367]
            }]]
        }

        self.validate_groundtruth_response("image_label_area_select", body)

    def test_groundtruth_uri_ilas_invalid_key(self):
        body = {
            "not_uri": [[{
                "entity_name": 0,
                "entity_type": "gate",
                "entity_coords": [275, 184, 454, 183, 453, 366, 266, 367]
            }]]
        }

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_area_select", body)

    def test_groundtruth_uri_ilas_invalid_value(self):
        body = {"https://domain.com/file1.jpeg": [[True]]}

        with self.assertRaises(schematics.exceptions.BaseError):
            self.validate_groundtruth_response("image_label_area_select", body)

    def test_taskdata_empty(self):
        """ should raise if taskdata_uri contains no entries """
        uri = "https://uri.com"
        manifest = {"taskdata_uri": uri}
        body = []

        self.register_http_response(uri, manifest, body)

        with self.assertRaises(schematics.exceptions.BaseError):
            basemodels.validate_manifest_uris(manifest)

    def test_taskdata_invalid_format(self):
        """ should raise if taskdata_uri contains object instead of array """
        uri = "https://uri.com"
        manifest = {"taskdata_uri": uri}
        body = {"key": [1, 2, 3]}

        self.register_http_response(uri, manifest, body)

        with self.assertRaises(schematics.exceptions.BaseError):
            basemodels.validate_manifest_uris(manifest)

    def test_taskdata_uri_valid(self):
        uri = "https://uri.com"
        manifest = {"taskdata_uri": uri}
        body = [{
            "task_key": "407fdd93-687a-46bb-b578-89eb96b4109d",
            "datapoint_uri": "https://domain.com/file1.jpg",
            "datapoint_hash": "f4acbe8562907183a484498ba901bfe5c5503aaa"
        },
                {
                    "task_key": "20bd4f3e-4518-4602-b67a-1d8dfabcce0c",
                    "datapoint_uri": "https://domain.com/file2.jpg",
                    "datapoint_hash": "f4acbe8562907183a484498ba901bfe5c5503aaa"
                }]

        self.register_http_response(uri, manifest, body)

        basemodels.validate_manifest_uris(manifest)

    def test_taskdata_uri_invalid(self):
        uri = "https://uri.com"
        manifest = {"taskdata_uri": uri}
        body = [{"task_key": "not_uuid", "datapoint_uri": "not_uri"}]

        self.register_http_response(uri, manifest, body)

        with self.assertRaises(schematics.exceptions.BaseError):
            basemodels.validate_manifest_uris(manifest)

    def test_groundtruth_and_taskdata_valid(self):
        taskdata_uri = "https://td.com"
        groundtruth_uri = "https://gt.com"
        manifest = {
            "taskdata_uri": taskdata_uri,
            "groundtruth_uri": groundtruth_uri,
            "request_type": "image_label_binary"
        }

        taskdata = [{
            "task_key": "407fdd93-687a-46bb-b578-89eb96b4109d",
            "datapoint_uri": "https://domain.com/file1.jpg",
            "datapoint_hash": "f4acbe8562907183a484498ba901bfe5c5503aaa"
        },
                    {
                        "task_key": "20bd4f3e-4518-4602-b67a-1d8dfabcce0c",
                        "datapoint_uri": "https://domain.com/file2.jpg",
                        "datapoint_hash": "f4acbe8562907183a484498ba901bfe5c5503aaa"
                    }]

        groundtruth = {
            "https://domain.com/123/file1.jpeg": ["false", "false", "false"],
            "https://domain.com/456/file2.jpeg": ["false", "true", "false"],
        }

        self.register_http_response(taskdata_uri, manifest, taskdata)
        self.register_http_response(groundtruth_uri, manifest, groundtruth)

        basemodels.validate_manifest_uris(manifest)

    def test_mitl_in_internal_config(self):
        """ Test that mitl config can be part of the internal configuration """
        model = a_manifest().to_primitive()
        mitl_config = {
            "n_gt": 200,
            "min_tasks_in_job": 1000,
            "n_gt_sample_min": 1,
            "n_gt_sample_max": 3,
            "task_max_repeats": 25,
            "max_tasks_in_job": 36000,
            "model_id": "ResNext50_32x4d",
            "task_selection_id": "MinMargin",
            "requester_min_repeats": 12,
            "requester_max_repeats": 25,
            "stop_n_active": 1000,
            "requester_accuracy_target": 0.8,
            "nested_config": {
                "value_a": 1,
                "value_b": 2
            }
        }

        model["internal_config"]["mitl"] = mitl_config
        manifest = basemodels.Manifest(model)
        manifest.validate()
        self.assertTrue(True)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("urllib3").setLevel(logging.INFO)
    unittest.main()
