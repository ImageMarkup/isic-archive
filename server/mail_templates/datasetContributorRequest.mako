<%include file="_header.mako"/>

<p>
This is an automated message from ISIC Archive.
You are receiving this message because you are
 a moderator of the "${group['name']}" group.
</p>

<p>
User <b>${user['login']}</b>
(<b><a href="mailto:${user['email']}">${user['firstName']} ${user['lastName']}</a></b>)
requested access to contribute datasets.
</p>

<p>
To approve or deny the request, visit the "${group['name']}" group page:
<br>
<a href="${host}/girder#group/${group['_id']}/pending">${host}/girder#group/${group['_id']}/pending</a>
</p>

<%include file="_footer.mako"/>
