<%inherit file="${context.get('baseTemplateFilename')}"/>

<%block name="docsBody">
## Use inline styles to override Swagger UI's reset.css
<p>Thank you for visiting the ${brandName | h} API! A summary of how to
accomplish the most common tasks is provided here:</p>

<p style="font-weight: bold">Retrieving a List of Images</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/image</span> endpoint.</p>
</div>

<p style="font-weight: bold">Retrieving a List of Current Studies</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/study</span> endpoint.</p>
</div>

<p style="font-weight: bold">Retrieving Image Metadata</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/image/{id}</span> endpoint, with the "_id" value from the data provided by
    the <span style="font-family: monospace">/image</span> endpoint. Data can be returned for only one image at a time.</p>
</div>

<p style="font-weight: bold">Download an Image</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/image/{id}/download</span> endpoint, with the "_id" value from the data
    provided by the <span style="font-family: monospace">/image</span> endpoint. Data can be returned for only one image at a
    time.</p>
</div>

<p style="font-weight: bold">Download Image Superpixel Data</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/image/{id}/superpixels</span> endpoint, with the "_id" value from the data
    provided by the <span style="font-family: monospace">/image</span> endpoint. Data can be returned for only one image at a
    time.</p>
</div>

<p style="font-weight: bold">Download a Segmentation Mask</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/segmentation</span> endpoint, with the "_id" value from the data provided
    by the <span style="font-family: monospace">/image</span> endpoint. In the data returned, retrieve the "_id" value for the
    desired segmentation mask, and use that value with the <span style="font-family: monospace">/segmentation/{id}/mask</span>
    endpoint. Data can be returned for only one mask at a time.</p>
</div>

<p style="font-weight: bold">Download an Annotation Mask</p>
<div style="margin: 15px">
    <p>Use the <span style="font-family: monospace">/study</span> endpoint to get a list of studies. For the desired study, use
    the "_id" variable with the <span style="font-family: monospace">/annotation</span> endpoint to get a list of annotations
    for that given study. From the list of annotations, select the "_id"
    (annotationId) variable of the desired annotation and use the
    <span style="font-family: monospace">/annotation/{annotationId}</span>
    endpoint to get a list of feature markups for that annotation. You can
    then use the annotationId and the feature name with the
    <span style="font-family: monospace">/annotation/{annotationId}/markup/{featureId}</span> endpoint to download a markup
    mask. Data can be returned for only one mask at a time.</p>
</div>
</%block>
