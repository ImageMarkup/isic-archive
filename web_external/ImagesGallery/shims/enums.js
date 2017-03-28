isic.FACET_SCHEMA = {
    'folderId': {
        FacetView: isic.views.ImagesFacetHistogramDatasetView,
        coerceToType: 'objectid',
        title: 'Dataset'
    },
    'meta.clinical.benign_malignant': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        title: 'Benign or Malignant'
    },
    'meta.clinical.age_approx': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Approximate Age',
        lowBound: 0,
        highBound: 90,
        numBins: 9
    },
    'meta.clinical.sex': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        title: 'Sex'
    },
    'meta.clinical.diagnosis_confirm_type': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        title: 'Type of Diagnosis'
    },
    'meta.clinical.diagnosis': {
        FacetView: isic.views.ImagesFacetCategoricalView,
        coerceToType: 'string',
        title: 'Lesion Diagnosis'
    },
    'meta.clinical.clin_size_long_diam_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Clinical Size - Longest Diameter (mm)',
        lowBound: 0,
        highBound: 110,
        numBins: 11
    },
    'meta.clinical.personal_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        title: 'Personal History of Melanoma'
    },
    'meta.clinical.family_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        coerceToType: 'string',
        title: 'Family History of Melanoma'
    }
};
