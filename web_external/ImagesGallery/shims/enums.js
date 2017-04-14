isic.FACET_SCHEMA = {
    'folderId': {
        FacetView: isic.views.ImagesFacetCategoricalDatasetView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'objectid',
        title: 'Dataset',
        collapsed: true
    },
    'meta.clinical.benign_malignant': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Benign or Malignant',
        collapsed: true
    },
    'meta.clinical.age_approx': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.IntervalFacetFilter,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Approximate Age',
        lowBound: 0,
        highBound: 90,
        numBins: 9,
        collapsed: true
    },
    'meta.clinical.sex': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Sex',
        collapsed: true
    },
    'meta.clinical.diagnosis_confirm_type': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Type of Diagnosis',
        collapsed: true
    },
    'meta.clinical.diagnosis': {
        FacetView: isic.views.ImagesFacetCategoricalView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Lesion Diagnosis',
        collapsed: true
    },
    'meta.clinical.clin_size_long_diam_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.IntervalFacetFilter,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Clinical Size - Longest Diameter (mm)',
        lowBound: 0,
        highBound: 110,
        numBins: 11,
        collapsed: true
    },
    'meta.clinical.personal_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Personal History of Melanoma',
        collapsed: true
    },
    'meta.clinical.family_hx_mm': {
        FacetView: isic.views.ImagesFacetHistogramView,
        FacetFilter: isic.collections.CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Family History of Melanoma',
        collapsed: true
    },
    'meta.tags': {
        FacetView: isic.views.ImagesFacetCategoricalTagsView,
        FacetFilter: isic.collections.TagsCategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Tags',
        collapsed: true
    }
};
