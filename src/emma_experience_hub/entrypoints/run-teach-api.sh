#!/bin/bash

function start_perception_api() {
	# Go to the perception folder
	cd './perception/' || exit

	export DEVICE_ID=0

	# Run the API using the correct venv
	.venv/bin/python src/emma_perception/commands/run_server.py \
		--config_file "$PERCEPTION_CONFIG_FILE" \
		MODEL.WEIGHT "$PERCEPTION_MODEL_FILE" \
		MODEL.ROI_HEADS.NMS_FILTER "1" \
		MODEL.ROI_HEADS.SCORE_THRESH "0.2" \
		TEST.IGNORE_BOX_REGRESSION "False"
}

function start_policy_api() {
	# Go to the policy folder
	cd './policy/' || exit

	# Run the API using the correct venv
	.venv/bin/python src/emma_policy/commands/run_teach_api.py \
		--data_dir /data \
		--images_dir /images \
		--split "$SPLIT" \
		--model_checkpoint_path "$POLICY_MODEL_FILE" \
		--max_frames 32
}

if [[ -n $ONLY_PERCEPTION ]]; then
	# Start the perception API
	start_perception_api
else
	# Start the Perception API
	start_perception_api &

	# Start the Policy API
	start_policy_api
fi
