from girder.utility import server as girder_server
girder_server.configureServer()

from girder.plugins.isic_archive.models.annotation import Annotation  # noqa: E402
from girder.plugins.isic_archive.models.featureset import Featureset  # noqa: E402
from girder.plugins.isic_archive.models.study import Study  # noqa: E402

featureMap = {
    '59e77183d831136981ef6af1': {  # MFE Featureset (version 3)
        'annular_granular_pattern_grey_dots': 'Dots : Annular-granular pattern',
        'asymmetric_pigmented_follicular_openings':
            'Circles & Semicircles : Asymmetric follicular openings',
        'blue_white_veil': 'Structureless : Blue-whitish veil',
        'concentric_circles': 'Circles & Semicircles : Circle within a circle',
        'globules_irregular': 'Globules / Clods : Irregular',
        'globules_regular': 'Globules / Clods : Regular',
        'milky_red_areas': 'Structureless : Milky red areas',
        'pigment_network_atypical': 'Network : Atypical pigment network / Reticulation',
        'pseudonetwork': 'Structureless : Pseudonetwork',
        'regression_scarlike_depigmentation': 'Regression structures : Scarlike depigmentation',
        'shiny_white_structures': 'Shiny white structures : Shiny white streaks',
        'streaks_pseudopods': 'Lines : Pseudopods',
        'tan_peripheral_structureless_area': 'Structureless : Structureless brown (tan)'
    },
    '58b0a9ecd831137d0a388969': {  # ISIC EASY Featureset (version 1.1)
        'angulated_lines': 'Lines : Angulated lines / Polygons / Zig-zag pattern',
        'blood_vessels_morphology_coiled': 'Vessels : Corkscrew',
        'blood_vessels_morphology_dots': 'Vessels : Dotted',
        'blood_vessels_morphology_polymorphous': 'Vessels : Polymorphous',
        'blood_vessels_morphology_serpentine': 'Vessels : Linear irregular',
        'blotch_irregular': 'Structureless : Blotch irregular',
        'blotch_regular': 'Structureless : Blotch regular',
        'blue_white_veil': 'Structureless : Blue-whitish veil',
        'dots_irregular': 'Dots : Irregular',
        'dots_regular': 'Dots : Regular',
        'globules_cobblestone_pattern': 'Globules / Clods : Cobblestone pattern',
        'globules_irregular': 'Globules / Clods : Irregular',
        'globules_regular': 'Globules / Clods : Regular',
        'globules_rim_brown_globules': 'Globules / Clods : Rim of brown globules',
        'milky_red_areas':  # Milky-red areas : Structureless zone, pink
            'Structureless : Milky red areas',
        'milky_red_globules':  # Milky-red areas : Clods, pink and small
            'Globules / Clods : Milky red',
        'negative_network': 'Network : Negative pigment network',
        'patterns_homogeneous_pattern': 'Pattern : Homogeneous : NOS',
        'patterns_starburst_pattern': 'Pattern : Starburst',
        'pigment_network_atypical': 'Network : Atypical pigment network / Reticulation',
        'pigment_network_typical': 'Network : Typical pigment network / Reticulation',
        'regression_peppering_irregular': 'Regression structures : Peppering / Granularity',
        'regression_scarlike_depigmentation': 'Regression structures : Scarlike depigmentation',
        'shiny_white_structures': 'Shiny white structures : NOS',
        'streaks_pseudopods': 'Miscellaneous : Pseudopods',
        'streaks_radial_streaming': 'Miscellaneous : Radial streaming',
        'tan_peripheral_structureless_area': 'Structureless : Structureless brown (tan)'
    },
    '59b97e72d83113146038f6aa': {  # ISIC EASY Featureset (version 1.2)
        'angulated_lines': 'Lines : Angulated lines / Polygons / Zig-zag pattern',
        'blood_vessels_morphology_comma': 'Vessels : Comma',
        'blood_vessels_morphology_corkscrew': 'Vessels : Corkscrew',
        'blood_vessels_morphology_dots': 'Vessels : Dotted',
        'blood_vessels_morphology_polymorphous': 'Vessels : Polymorphous',
        'blood_vessels_morphology_serpentine': 'Vessels : Linear irregular',
        'blotch_irregular': 'Structureless : Blotch irregular',
        'blotch_regular': 'Structureless : Blotch regular',
        'blue_white_veil': 'Structureless : Blue-whitish veil',
        'dots_irregular': 'Dots : Irregular',
        'dots_regular': 'Dots : Regular',
        'globules_cobblestone_pattern': 'Globules / Clods : Cobblestone pattern',
        'globules_irregular': 'Globules / Clods : Irregular',
        'globules_regular': 'Globules / Clods : Regular',
        'globules_rim_brown_globules': 'Globules / Clods : Rim of brown globules',
        'milky_red_areas':  # Milky-red areas : Structureless zone, pink
            'Structureless : Milky red areas',
        'milky_red_globules':  # Milky-red areas : Clods, pink and small
            'Globules / Clods : Milky red',
        'negative_network': 'Network : Negative pigment network',
        'patterns_homogeneous_pattern': 'Pattern : Homogeneous : NOS',
        'patterns_starburst_pattern': 'Pattern : Starburst',
        'pigment_network_atypical': 'Network : Atypical pigment network / Reticulation',
        'pigment_network_broadened': 'Network : Broadened pigment network / Reticulation',
        'pigment_network_delicate': 'Network : Delicate Pigment Network / Reticulation',
        'pigment_network_typical': 'Network : Typical pigment network / Reticulation',
        'regression_peppering_irregular': 'Regression structures : Peppering / Granularity',
        'regression_scarlike_depigmentation': 'Regression structures : Scarlike depigmentation',
        'shiny_white_structures': 'Shiny white structures : NOS',
        'streaks_pseudopods': 'Miscellaneous : Pseudopods',
        'streaks_radial_streaming': 'Miscellaneous : Radial streaming',
        'tan_peripheral_structureless_area': 'Structureless : Structureless brown (tan)'
    },
    '5ac72fb61165973043ccd539': {  # Challenge Part 2 (version 1)
        'milia_like_cyst': 'Miscellaneous : Milia-like cysts, cloudy or starry',
        'negative_network': 'Network : Negative pigment network',
        'pigment_network': 'Network : Typical pigment network / Reticulation',
        'streaks': 'Lines : Streaks',
        'globules': 'Globules / Clods : NOS'
    },
    '5a32cd991165975cf58a469b': {  # ISIC InterRater Agreement [MasterFeatures 12/2017](version 0.2)
        'angulated_lines_polygons_zig_zag_pattern':
            'Lines : Angulated lines / Polygons / Zig-zag pattern',
        'blood_spots': 'Nail lesions : Blood spots',
        'blotch_irregular': 'Structureless : Blotch irregular',
        'blotch_regular': 'Structureless : Blotch regular',
        'blue_gray_ovoid_nests': 'Globules / Clods : Blue-gray ovoid nests',
        'blue_whitish_veil': 'Structureless : Blue-whitish veil',
        'branched_streaks': 'Lines : Branched streaks',
        'central_white_patch': 'Structureless : Central white patch',
        'circle_within_a_circle': 'Circles & Semicircles : Circle within a circle',
        'circles_brown': 'Circles & Semicircles : Brown',
        'circles_nos': 'Circles & Semicircles : NOS',
        'circles_white': 'Circles & Semicircles : White',
        'comedo_like_openings': 'Globules / Clods : Comedo-like openings',
        'concentric_structures': 'Globules / Clods : Concentric',
        'crypts': 'Lines : Crypts',
        'dots_black': 'Dots : Black',
        'dots_blue_gray': 'Dots : Blue-gray',
        'dots_brown': 'Dots : Brown',
        'dots_irregular': 'Dots : Irregular',
        'dots_linear': 'Dots : Linear',
        'dots_nos': 'Dots : NOS',
        'dots_regular': 'Dots : Regular',
        'dots_targetoid': 'Dots : Targetoid',
        'feature_nos': None,
        'fissures': 'Miscellaneous : Fissures',
        'globules_blue_': 'Globules / Clods : Blue',
        'globules_cobblestone_pattern': 'Globules / Clods : Cobblestone pattern',
        'globules_irregular': 'Globules / Clods : Irregular',
        'globules_nos': 'Globules / Clods : NOS',
        'globules_regular': 'Globules / Clods : Regular',
        'globules_rim_of_brown_globules': 'Globules / Clods : Rim of brown globules',
        'globules_white': 'Globules / Clods : White',
        'lacunae_black_': 'Globules / Clods : Lacunae : Black',
        'lacunae_blue_': 'Globules / Clods : Lacunae : Blue',
        'lacunae_red_': 'Globules / Clods : Lacunae : Red',
        'lacunae_red_purple': 'Globules / Clods : Lacunae : Red-purple',
        'leaflike_area': 'Globules / Clods : Leaflike area',
        'lines_nos': 'Lines : NOS',
        'milia_like_cysts': 'Globules / Clods : Milia-like cysts',
        'milky_red_areas': 'Structureless : Milky red areas',
        'milky_red_globules': 'Globules / Clods : Milky red',
        'moth_eaten_border': 'Miscellaneous : Moth-eaten border',
        'pattern_cerebriform': 'Pattern : Cerebriform',
        'pattern_fingerprint': 'Pattern : Fingerprint',
        'pattern_homogeneous_blue': 'Pattern : Homogeneous : Blue',
        'pattern_homogeneous_brown': 'Pattern : Homogeneous : Brown',
        'pattern_homogeneous_nos': 'Pattern : Homogeneous : NOS',
        'pattern_homogeneous_pink': 'Pattern : Homogeneous : Pink',
        'pattern_nos': 'Pattern : NOS',
        'pattern_starburst': 'Pattern : Starburst',
        'pattern_strawberry': 'Pattern : Strawberry',
        'pigment_network_negative_network': 'Network : Negative pigment network',
        'pigment_network_nos': 'Network : NOS',
        'pigment_network_reticulation_atypical':
            'Network : Atypical pigment network / Reticulation',
        'pigment_network_reticulation_broadened':
            'Network : Broadened pigment network / Reticulation',
        'pigment_network_reticulation_delicate':
            'Network : Delicate Pigment Network / Reticulation',
        'pigment_network_reticulation_typical': 'Network : Typical pigment network / Reticulation',
        'pseudopods': 'Lines : Pseudopods',
        'radial_streaming': 'Lines : Radial streaming',
        'regression_structures_nos': 'Regression structures : NOS',
        'regression_structures_peppering_granularity':
            'Regression structures : Peppering / Granularity',
        'regression_structures_scarlike_depigmentation':
            'Regression structures : Scarlike depigmentation',
        'ridges': 'Miscellaneous : Ridges',
        'rosettes': 'Shiny white structures : Rosettes',
        'scale': 'Miscellaneous : Scale',
        'shiny_white_blotches_and_strands':
            'Shiny white structures : Shiny white blotches and strands',
        'shiny_white_streaks': 'Shiny white structures : Shiny white streaks',
        'shiny_white_structures_nos': 'Shiny white structures : NOS',
        'spoke_wheel_area': 'Miscellaneous : Spoke wheel area',
        'streaks': 'Lines : Streaks',
        'string_of_pearls': 'Vessels : String of pearls',
        'structureless_brown_tan_eccentric': 'Structureless : Structureless brown (tan)',
        'structureless_nos': 'Structureless : NOS',
        'ulceration_erosion': 'Miscellaneous : Ulceration / Erosion',
        'vessels_arborizing': 'Vessels : Arborizing',
        'vessels_comma': 'Vessels : Comma',
        'vessels_corckscrew': 'Vessels : Corkscrew',
        'vessels_crown': 'Vessels : Crown',
        'vessels_dotted': 'Vessels : Dotted',
        'vessels_glomerular': 'Vessels : Glomerular',
        'vessels_hairpin': 'Vessels : Hairpin',
        'vessels_linear_irregular': 'Vessels : Linear irregular',
        'vessels_monomorphous': 'Vessels : Monomorphous',
        'vessels_nos': 'Vessels : NOS',
        'vessels_polymorphous': 'Vessels : Polymorphous',
        'vessels_targetoid': 'Vessels : Targetoid',
    },
    '573f09bd9fc3c132505c0ee6': {},  # Lesion Classification (version 1)
    '58d52fb3d831133741859b57': {},  # Lesion Classification (version 2)
}

for study in Study().find():
    print study['name']

    featureset = Featureset().load(study['meta']['featuresetId'])
    del study['meta']['featuresetId']

    study['meta']['questions'] = [
        {
            'id': ' : '.join(globalFeature['name']),
            'type': 'select',
            'choices': [
                globalFeatureOption['name']
                for globalFeatureOption in globalFeature['options']
            ]
        }
        for globalFeature in featureset['globalFeatures']
    ]
    study['meta']['features'] = [
        {
            'id': featureMap[str(featureset['_id'])][localFeature['id']]
        }
        for localFeature in featureset['localFeatures']
        # drop "feature_nos" from studies
        if featureMap[str(featureset['_id'])][localFeature['id']] is not None
    ]
    # Study().validate(study)
    Study().save(study)

    for annotation in Annotation().find({'studyId': study['_id']}):
        print ' ', annotation['_id']

        newResponses = {}
        for oldResponseId, oldResponseValue in annotation['responses'].viewitems():
            for globalFeature in featureset['globalFeatures']:
                if globalFeature['id'] == oldResponseId:
                    newResponseId = ' : '.join(globalFeature['name'])

                    for globalFeatureOption in globalFeature['options']:
                        if globalFeatureOption['id'] == oldResponseValue:
                            newResponseValue = globalFeatureOption['name']
                            break
                    else:
                        raise Exception

                    break
            else:
                raise Exception

            newResponses[newResponseId] = newResponseValue
        annotation['responses'] = newResponses

        newMarkups = {}
        for oldMarkupId, oldMarkupValue in annotation['markups'].viewitems():
            for localFeature in featureset['localFeatures']:
                if localFeature['id'] == oldMarkupId:
                    newMarkupId = featureMap[str(featureset['_id'])][localFeature['id']]
                    break
            else:
                raise Exception

            if newMarkupId is None:
                # drop "feature_nos" from markup
                continue
            newMarkups[newMarkupId] = oldMarkupValue
        annotation['markups'] = newMarkups
        # Annotation().validate(annotation)
        Annotation().save(annotation, validate=False)
