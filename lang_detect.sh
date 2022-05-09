ltf_raw=$1
ltf_translated=$2
parent_child_tab=$3
query_root=$4
output_dir=$5
gpu_device=$6

rsd_raw=${output_dir}/rsd
output_dir_en=${output_dir}/en
output_dir_ru=${output_dir}/ru
output_dir_es=${output_dir}/es
# generate RSD
docker run --rm -v ${rsd_raw}:${rsd_raw} -v ${ltf_raw}:${ltf_raw} blendernlp/covid-claim-radar:ke \
    perl /preprocessing/ltf2rsd.perl -o ${rsd_raw} ${ltf_raw}
# detect language
docker run --rm -v ${rsd_raw}:${rsd_raw} -v ${ltf_raw}:${ltf_raw} -v ${output_dir}:${output_dir} -v ${parent_child_tab}:${parent_child_tab} blendernlp/covid-claim-radar:ke \
    /opt/conda/envs/genie/bin/python /preprocessing/preprocess_detect_languages.py \
    ${rsd_raw} ${ltf_raw} ${output_dir} --parent_child_tab_path ${parent_child_tab} --langs en ru es
# generate translated english RSD for russian / spanish
docker run --rm -v ${output_dir_ru}:${output_dir_ru} -v ${ltf_translated}:${ltf_translated} blendernlp/covid-claim-radar:ke \
    /opt/conda/envs/genie/bin/python /preprocessing/mt_converter.py \
    --ltf_dir_raw ${output_dir_ru}/ltf_raw \
    --ltf_dir_trans_isi ${ltf_translated} \
    --rsd_dir_trans_en ${output_dir_ru}/rsd \
    --mapping_dir ${output_dir_ru}
docker run --rm -v ${output_dir_es}:${output_dir_es} -v ${ltf_translated}:${ltf_translated} blendernlp/covid-claim-radar:ke \
    /opt/conda/envs/genie/bin/python /preprocessing/mt_converter.py \
    --ltf_dir_raw ${output_dir_es}/ltf_raw \
    --ltf_dir_trans_isi ${ltf_translated} \
    --rsd_dir_trans_en ${output_dir_es}/rsd \
    --mapping_dir ${output_dir_es}
# generate translated english LTF for russian / spanish
docker run --rm -v ${output_dir_ru}:${output_dir_ru} blendernlp/covid-claim-radar:ke \
    /opt/conda/envs/genie/bin/python /preprocessing/rsd2ltf.py --seg_option nltk+linebreak --tok_option nltk_wordpunct --extension .rsd.txt \
    ${output_dir_ru}/rsd ${output_dir_ru}/ltf
docker run --rm -v ${output_dir_es}:${output_dir_es} blendernlp/covid-claim-radar:ke \
    /opt/conda/envs/genie/bin/python /preprocessing/rsd2ltf.py --seg_option nltk+linebreak --tok_option nltk_wordpunct --extension .rsd.txt \
    ${output_dir_es}/rsd ${output_dir_es}/ltf

# run extract.sh
./extract.sh en ${output_dir_en} ${query_root} ${parent_child_tab} ${gpu_device}
./extract.sh ru ${output_dir_ru} ${query_root} ${parent_child_tab} ${gpu_device}
./extract.sh es ${output_dir_es} ${query_root} ${parent_child_tab} ${gpu_device}