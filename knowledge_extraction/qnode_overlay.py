import ujson as json
from collections import defaultdict
import os

def format_type(raw_type):
    type_formatted = raw_type.lower().replace('.unspecified', '')
    type_formatted = type_formatted.replace(
                'movement.transportperson', 'movement.transportation'
            ).replace(
                'movement.transportartifact', 'movement.transportation'
            ).replace(
                'transaction.transfermoney','transaction.exchangebuysell'
            ).replace(
                'transaction.transferownership','transaction.exchangebuysell'
            ).replace(
                'transaction.transferownership','transaction.exchangebuysell'
            ).replace(
                'transaction.transaction', 'transaction.exchangebuysell'
            ).replace(
                'manufacture.artifact', 'artifactexistence.manufactureassemble'
            ).replace(
                'business.start', 'government.formation.startgpe'
            ).replace(
                'business.end', 'personnel.endposition'
            ).replace(
                'justice.appeal', 'justice.judicialconsequences'
            ).replace(
                'justice.fine', 'justice.judicialconsequences'
            ).replace(
                'justice.sue', 'justice.initiatejudicialprocess'
            ).replace(
                'justice.arrestjail', 'justice.arrestjaildetain'
            ).replace(
                'life.injure.illnessdegredationsickness', 'life.illness'
            ).replace(
                'business.declarebankruptcy', 'artifactExistence.damagedestroydisabledismantle'
            ).replace(
                'personnel.nominate', 'personnel.elect'
            ).replace(
                'justice.pardon', 'justice.releaseparole'
            ).replace(
                'business.merge', 'government.formation.mergegpe'
            ).replace(
                'disaster.accidentcrash.accidentcrash', 'disaster.crash'
            )
    if 'life.marry' in type_formatted or 'life.beborn' in type_formatted or 'life.divorce' in type_formatted:
        return None
    return type_formatted

def format_role(raw_role):
    role_formatted = raw_role.replace(
            'Participant', 'Communicator_ParticipantArg1'
        ).replace(
            'Agent', 'Transporter_Killer_AgentWhoIsSanitizing_Jailer_Founder_Executioner_JudgeCourt_Injurer'
        ).replace(
            'Artifact', 'PassengerArtifact'
        ).replace(
            'Thing', 'AcquiredEntity_ThingPrevented'
        ).replace(
            'Broadcaster', 'Communicator'
        ).replace(
            'Person', 'PassengerArtifact_Employee_Detainee_Defendant'
        ).replace(
            'Organization', 'PlaceOfEmployment_GPE_Artifact_ParticipantArg2'
        ).replace(
            'Manufacturer', 'ManufacturerAssembler'
        ).replace(
            'Assessed', 'ThingAssessed'
        ).replace(
            'Treater', 'Healer'
        ).replace(
            'Washer', 'WasherWhoIsWashing'
        ).replace(
            'Audience', 'Recipient'
        ).replace(
            'Created', 'ThingCreated'
        ).replace(
            'Elector', 'Voter'
        ).replace(
            'Elect', 'Voter'
        ).replace(
            'Instrument', 'Vehicle_MedicalIssue'
        ).replace(
            'Mutating', 'ThingMutating'
        ).replace(
            'worn', 'ThingWorn'
        ).replace(
            'object', 'SanitizedObject'
        ).replace(
            'Adjudicator', 'Prosecutor_JudgeCourt'
        ).replace(
            'Plaintiff', 'Defendant'
        ).replace(
            'Contaminated', 'ThingContaminated'
        ).replace(
            'Prosecutor', 'JudgeCourt'
        ).replace(
            'Washed', 'ThingWashed'
        ).replace(
            'Creator', 'ManufacturerAssembler'
        ).replace(
            'Nominee', 'Candidate'
        ).replace(
            'Nominator', 'Voter'
        ).replace(
            'Material', 'ComponentsMaterials'
        )
    return role_formatted

def format_relation(rel_type):
    rel_formatted = rel_type.replace(
        'APORA',
        'ArtifactPoliticalOrganizationReligiousAffiliation'
    ).replace(
        'MORE',
        'MemberOriginReligionEthnicity'
    ).replace(
        'Physical.OrganizationHeadquarter',
        'Physical.OrganizationHeadquarters.OrganizationHeadquarters'
    ).replace(
        'Physical.OrganizationLocationOrigin',
        'Physical.OrganizationHeadquarters.OrganizationHeadquarters'
    ).replace(
        'Physical.Resident',
        'Physical.Resident.Resident'
    ).replace(
        'PersonalSocial.Family',
        'PersonalSocial.Relationship'
    ).replace(
        'PersonalSocial.Business',
        'PersonalSocial.Relationship.Political'
    ).replace(
        'PersonalSocial.Unspecified',
        'PersonalSocial.Relationship'
    ).replace(
        'OrganizationAffiliation.StudentAlum',
        'OrganizationAffiliation.EmploymentMembership'
    ).replace(
        'OrganizationAffiliation.InvestorShareholder',
        'OrganizationAffiliation.Leadership'
    ).replace(
        'PartWhole.Membership',
        'PartWhole.Subsidiary.OrganizationSubsidiary'
    ).replace(
        'OrganizationAffiliation.Ownership',
        'OrganizationAffiliation.Leadership'
    ).replace(
        'OrganizationAffiliation.Founder',
        'OrganizationAffiliation.Founder.Founder'
    )
    return rel_formatted

def load_xpo(xpo_json):
    xpo_data = json.load(open(xpo_json))
    ontology_json = defaultdict(lambda : defaultdict(lambda : defaultdict()))
    for Qnode in xpo_data['events']:
        qnode_id = xpo_data['events'][Qnode]['wd_qnode'] if 'wd_qnode' in xpo_data['events'][Qnode] else xpo_data['events'][Qnode]['wd_pnode']
        if 'ldc_types' not in xpo_data['events'][Qnode]:
            continue
        for LDC_type in xpo_data['events'][Qnode]['ldc_types']:
            ldc_type_name = format_type(LDC_type['name']).replace('justice.arrestjaildetaindetain', 'justice.arrestjaildetain')
            ldc_type_name_subtype = ldc_type_name.split('.')[-1]
            ontology_json['event'][ldc_type_name]['qnode'] = qnode_id
            ontology_json['event_subtype'][ldc_type_name_subtype]['qnode'] = qnode_id
            if 'ldc_arguments' in LDC_type:
                for LDC_arg in LDC_type['ldc_arguments']:
                    ldc_arg_name = LDC_arg['ldc_name'].strip()
                    ontology_json['event_arg'][qnode_id][ldc_arg_name] = LDC_arg['dwd_arg_name']
        # break
    # print(ontology_json['event'])
    # ontology_json['event']['life.beborn']['qnode'] = 
    # ontology_json['event']['movement.transportperson']['qnode'] = 'Q7590'
    # ontology_json['event_args']['movement.transportperson_'+ldc_arg_name]['qnode'] = qnode_id
    
    for Qnode in xpo_data['relations']:
        qnode_id = xpo_data['relations'][Qnode]['wd_qnode'] if 'wd_qnode' in xpo_data['relations'][Qnode] else xpo_data['relations'][Qnode]['wd_pnode']
        for LDC_type in xpo_data['relations'][Qnode]['ldc_types']:
            ldc_type_name = LDC_type['name'].replace('.Unspecified', '')
            ontology_json['relation'][ldc_type_name]['qnode'] = qnode_id
            for LDC_arg in LDC_type['ldc_arguments']:
                # ldc_arg_name = LDC_arg['ldc_name'].strip()
                dwd_arg_name = LDC_arg['dwd_arg_name']
                # if dwd_arg_name.startswith('A0'):
                ontology_json['relation_arg'][qnode_id][dwd_arg_name[:2]] = LDC_arg['dwd_arg_name']
        # break
    # for type in ontology_json['relation']:
    #     print(type)

    for Qnode in xpo_data['entities']:
        qnode_id = xpo_data['entities'][Qnode]['wd_qnode'] if 'wd_qnode' in xpo_data['entities'][Qnode] else xpo_data['entities'][Qnode]['wd_pnode']
        for LDC_type in xpo_data['entities'][Qnode]['ldc_types']:
            ldc_type_name = LDC_type['name'].replace('.Unspecified', '')
            ontology_json['entity'][ldc_type_name] = qnode_id
            # for LDC_arg in LDC_type['ldc_arguments']:
            #     ldc_arg_name = LDC_arg['ldc_name']
            #     ontology_json['relation_args'][ldc_type_name+'_'+ldc_arg_name]['qnode'] = qnode_id
        # break

    
    return ontology_json

def xpo2tab(xpo_json, output_tab_dir):
    xpo_data = json.load(open(xpo_json))
    ontology_json = defaultdict(lambda : defaultdict(lambda : defaultdict()))
    writer = open(os.path.join(output_tab_dir, 'xpo_v4_event.tab'), 'w')
    for Qnode in xpo_data['events']:
        qnode_id = xpo_data['events'][Qnode]['wd_qnode'] if 'wd_qnode' in xpo_data['events'][Qnode] else xpo_data['events'][Qnode]['wd_pnode']
        if 'ldc_types' not in xpo_data['events'][Qnode]:
            continue
        qnode_name = xpo_data['events'][Qnode]['name']
        for LDC_type in xpo_data['events'][Qnode]['ldc_types']:
            ldc_type_name = LDC_type['name'] #.lower()
            writer.write(ldc_type_name + "\t" + qnode_id +"\t"+str(qnode_name))
            ontology_json['event'][ldc_type_name]['qnode'] = qnode_id
            if 'ldc_arguments' in LDC_type:
                for LDC_arg in LDC_type['ldc_arguments']:
                    ldc_arg_name = LDC_arg['ldc_name']
                    ontology_json['event_args'][ldc_type_name+'_'+ldc_arg_name]['qnode'] = qnode_id
                    dwd_arg_name = LDC_arg['dwd_arg_name']
                    print(ldc_arg_name, dwd_arg_name)
                    writer.write("\t"+ldc_arg_name + "\t" + str(dwd_arg_name))
            writer.write('\n')
        # break
    writer.flush()
    writer.close()
    for Qnode in xpo_data['relations']:
        qnode_id = xpo_data['relations'][Qnode]['wd_node']
        for LDC_type in xpo_data['relations'][Qnode]['ldc_types']:
            ldc_type_name = LDC_type['name'] #.lower()
            ontology_json['relation'][ldc_type_name]['qnode'] = qnode_id
            for LDC_arg in LDC_type['ldc_arguments']:
                ldc_arg_name = LDC_arg['ldc_name']
                ontology_json['relation_args'][ldc_type_name+'_'+ldc_arg_name]['qnode'] = qnode_id
        # break
    writer = open(os.path.join(output_tab_dir, 'xpo_v4_entity.tab'), 'w')
    for Qnode in xpo_data['entities']:
        qnode_id = xpo_data['entities'][Qnode]['wd_node']
        for LDC_type in xpo_data['entities'][Qnode]['ldc_types']:
            ldc_type_name = LDC_type['name'] #.replace('.Unspecified', '')
            ontology_json['entity'][ldc_type_name] = qnode_id
            writer.write(ldc_type_name + "\t" + qnode_id)
        # break
        writer.write('\n')
    writer.flush()
    writer.close()
    return ontology_json

# def template():
template={
    "origin": ("Origin of the Virus", "Who created the virus", "X created SARS-CoV-2"),
    "preventing": ("Curing/Preventing/Destroying the Virus", "Preventing the virus", "X prevents COVID-19"),
    "curing": ("Curing/Preventing/Destroying the Virus", "Curing the virus", "X cures COVID-19"),
    "transmitting": ("Transmitting the virus", "What transmits the virus", "X transmits / transfers COVID-19"),
    "destroying": ("Curing/Preventing/Destroying the Virus", "Destroying the virus", "X destroys COVID-19")
}
    # return template

if __name__ == '__main__':
    xpo_json = '/shared/nas/data/m1/manling2/aida_docker/docker_m18/postprocessing/params/xpo_v4_to_be_checked4.json'
    # ontology_json = load_xpo(xpo_json)
    # print(len(ontology_json['event'].keys()))

    output_tab_dir = '/shared/nas/data/m1/manling2/aida_docker/docker_m18/postprocessing/params/'
    xpo2tab(xpo_json, output_tab_dir)
