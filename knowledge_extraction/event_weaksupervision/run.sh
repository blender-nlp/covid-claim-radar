TASK=$1
ONEIE_OUTPUT_DIR=$2
OUTPUT_DIR=$3
ENRICHED_ENTITY_CS_FILE=$4
ARGUMENT_FILE=$5

if [ ! -d ${OUTPUT_DIR} ]
then
    mkdir -p ${OUTPUT_DIR}
fi

DETECT_CMD="/opt/conda/bin/python /event_weaksupervision/run_event_detection.py \
 --input-dir ${ONEIE_OUTPUT_DIR} \
 --output-dir ${OUTPUT_DIR} \
 --input-type doc \
 --resource-dir /event_weaksupervision/resources/models/covid"

MERGE_CMD="/opt/conda/bin/python /event_weaksupervision/convert_outputs.py \
 --input-dir ${ONEIE_OUTPUT_DIR} \
 --output-dir ${OUTPUT_DIR} \
 --input-type doc \
 --resource-dir /event_weaksupervision/resources/models/covid \
 --merged-ent-cs ${ENRICHED_ENTITY_CS_FILE}"

CONVERT_CMD="/opt/conda/bin/python /event_weaksupervision/run_conversion.py \
 --output-dir ${OUTPUT_DIR}"

if [ ${TASK} = "detect" ]
then
docker run -P --rm -i \
 -v ${ONEIE_OUTPUT_DIR}:${ONEIE_OUTPUT_DIR} \
 -v ${OUTPUT_DIR}:${OUTPUT_DIR} \
 -v ${ENRICHED_ENTITY_CS_FILE}:${ENRICHED_ENTITY_CS_FILE} \
 --gpus all fishinnorthernmostsea/event_weaksupervision:latest sh -c "${DETECT_CMD}"
elif [ ${TASK} = "merge" ]
then
cp ${ARGUMENT_FILE} ${OUTPUT_DIR}/docs.args.jsonl
docker run -P --rm -i \
 -v ${ONEIE_OUTPUT_DIR}:${ONEIE_OUTPUT_DIR} \
 -v ${OUTPUT_DIR}:${OUTPUT_DIR} \
 -v ${ENRICHED_ENTITY_CS_FILE}:${ENRICHED_ENTITY_CS_FILE} \
 -w /event_weaksupervision --gpus all fishinnorthernmostsea/event_weaksupervision sh -c "${MERGE_CMD} && ${CONVERT_CMD}"
else
    echo "option $1 not recogonized"
fi
