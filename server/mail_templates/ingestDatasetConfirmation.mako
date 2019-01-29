<%include file="_header.mako"/>

% if not isOriginalUploader:
<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
A user added a ZIP image batch to the ISIC Archive.
</div>
<p>For reference, here is the batch information:</p>
% else:
<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
Thank you for contributing a ZIP image batch to the ISIC Archive.
</div>
<p>For your records, here is the batch information:</p>
% endif

<table style="border-spacing: 0; border-collapse: collapse">
    <tbody>
        <tr>
            <th colspan="2">Dataset</th>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Name</td>
            <td style="padding: 5px;">${dataset['name']}</td>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Description</td>
            <td style="padding: 5px;">${dataset['description']}</td>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">License</td>
            <td style="padding: 5px;">${dataset['license']}</td>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Attribution</td>
            <td style="padding: 5px;">${dataset['attribution']}</td>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Owner</td>
            <td style="padding: 5px;">${dataset['owner']}</td>
        </tr>
        <tr>
            <th colspan="2">Batch</th>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Uploaded by</td>
            <td style="padding: 5px;">${user['firstName']} ${user['lastName']} &lt;<a href="mailto:${user['email']}">${user['email']}</a>&gt; (${user['login']})</td>
        </tr>
        <tr>
            <td style="padding: 5px; font-weight: bold;">Signature</td>
            <td style="padding: 5px;">${batch['signature']}</td>
        </tr>
    </tbody>
</table>

% if skippedFilenames:
    <h4>Skipped Files</h4>
    One or more files within your dataset was skipped, if you think this is a mistake contact admin@isic-archive.com:<br>
    % for skippedFilename in skippedFilenames:
        ${skippedFilename['privateMeta']['originalFilename']}
    % endfor
% endif

% if failedImages:
    <h4>Failures</h4>
    <br>One or more files within your dataset failed to be completely imported into the archive:<br>
    % for failedImage in failedImages:
        ${failedImage['privateMeta']['originalFilename']}<br>
    % endfor
% endif

% if isOriginalUploader:
<p>
The Terms of Use that you agreed to via electronic signature is available here:<br>
<a href="${host}#termsOfUse">${host}#termsOfUse</a>
</p>
% endif

<%include file="_footer.mako"/>
