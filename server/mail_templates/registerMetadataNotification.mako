<%include file="_header.mako"/>

<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
A user registered a metadata file with a dataset in the ISIC Archive.
</div>
<p>Here is the dataset information:</p>

<table style="border-spacing: 0px; border-collapse: collapse">
<tbody>
<tr>
<td style="padding: 5px; font-weight: bold;">Registered by</td>
<td style="padding: 5px;">${user['firstName']} ${user['lastName']} &lt;<a href="mailto:${user['email']}">${user['email']}</a>&gt; (${user['login']})</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Dataset</td>
<td style="padding: 5px;">${dataset['name']}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Dataset ID</td>
<td style="padding: 5px;">${dataset['_id']}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Metadata File Name</td>
<td style="padding: 5px;">${csvFile['name']}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Metadata File ID</td>
<td style="padding: 5px;">${csvFile['_id']}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Date</td>
<td style="padding: 5px;">${date}</td>
</tr>
</tbody>
</table>

<%include file="_footer.mako"/>
