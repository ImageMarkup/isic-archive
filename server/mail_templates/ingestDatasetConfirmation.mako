<%include file="_header.mako"/>

% if group:
<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
A user contributed a dataset to the ISIC Archive.
</div>
<p>For reference, here is the dataset information:</p>
% else:
<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
Thank you for contributing a dataset to the ISIC Archive.
</div>
<p>For your records, here is the dataset information:</p>
% endif

<table style="border-spacing: 0px; border-collapse: collapse">
<tbody>
<tr>
<td style="padding: 5px; font-weight: bold;">Uploaded by</td>
<td style="padding: 5px;">${user['firstName']} ${user['lastName']} &lt;<a href="mailto:${user['email']}">${user['email']}</a>&gt; (${user['login']})</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Name</td>
<td style="padding: 5px;">${name}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Owner</td>
<td style="padding: 5px;">${owner}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Description</td>
<td style="padding: 5px;">${description}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">License</td>
<td style="padding: 5px;">${license}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Signature</td>
<td style="padding: 5px;">${signature}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Attribution</td>
<td style="padding: 5px;">${attribution}</td>
</tr>
</tbody>
</table>

% if not group:
<p>
The Terms of Use that you agreed to via electronic signature is available here:<br>
<a href="${host}#termsOfUse">${host}#termsOfUse</a>
</p>
% endif

<%include file="_footer.mako"/>
