// TODO: there's probably a better way to import these...

isic.ENUMS = {};

isic.ENUMS.DEFAULT_INTERPRETATIONS = {
    'undefined': 'categorical',
    'null': 'categorical',
    boolean: 'categorical',
    integer: 'ordinal',
    number: 'ordinal',
    date: 'categorical',
    string: 'categorical',
    object: 'categorical'
};

isic.ENUMS.ATTRIBUTE_GENERALITY = [
    'object',
    'string',
    'number',
    'integer'
];

isic.ENUMS.FILTER_STATES = {
    NO_FILTERS: 0,
    FILTERED: 1,
    EXCLUDED: 2
};

isic.ENUMS.BIN_STATES = {
    INCLUDED: 0,
    EXCLUDED: 1,
    PARTIAL: 2
};

// TODO: It should be trivial to borrow code from Resonant Laboratory to
// autodetect this (requires an additional server endpoint)
isic.ENUMS.SCHEMA = {
    'folderId': {
        FacetView: isic.views.ImagesFacetHistogramDatasetView,
        coerceToType: 'objectid',
        humanName: 'Dataset'
    },
    'meta.clinical.benign_malignant': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        humanName: 'Benign or Malignant'
    },
    'meta.clinical.age': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'number',
        interpretation: 'ordinal',
        humanName: 'Age',
        lowBound: 0,
        highBound: 90,
        numBins: 9
    },
    'meta.clinical.sex': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        humanName: 'Sex'
    },
    'meta.clinical.diagnosis_confirm_type': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        humanName: 'Type of Diagnosis'
    },
    'meta.clinical.diagnosis': {
        FacetView: isic.views.ImagesFacetCategoricalView,
        coerceToType: 'string',
        humanName: 'Lesion Diagnosis'
    },
    'meta.clinical.clin_size_long_diam_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'number',
        interpretation: 'ordinal',
        humanName: 'Clinical Size - Longest Diameter (mm)',
        lowBound: 0,
        highBound: 110,
        numBins: 11
    },
    'meta.clinical.personal_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        humanName: 'Personal History of Melanoma'
    },
    'meta.clinical.family_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        humanName: 'Family History of Melanoma'
    }
};
