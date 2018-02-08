<%include file="_header.mako"/>

<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
A user requested to participate in a study in the ISIC Archive.
</div>
<p>Here are the details:</p>

<table style="border-spacing: 0px; border-collapse: collapse">
<tbody>
<tr>
<td style="padding: 5px; font-weight: bold;">User</td>
<td style="padding: 5px;">${user['firstName']} ${user['lastName']} &lt;<a href="mailto:${user['email']}">${user['email']}</a>&gt; (${user['login']})</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Study</td>
<td style="padding: 5px;">${study['name']}</td>
</tr>
<tr>
<td style="padding: 5px; font-weight: bold;">Study ID</td>
<td style="padding: 5px;">${study['_id']}</td>
</tr>
</tbody>
</table>
<p>

<p>
To approve or deny the request, visit the Studies page:
<br>
<a href="${host}/#studies">${host}/#studies</a>
</p>

<%include file="_footer.mako"/>
