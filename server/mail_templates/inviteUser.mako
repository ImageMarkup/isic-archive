<%include file="_header.mako"/>

<p>
Dear <b>${newUser['firstName']} ${newUser['lastName']}</b>,
</p>
<p>
You have been invited to use the ISIC Archive.
</p>
<p>
Please click the following link to finalize your account:<br>
<a href="${inviteUrl}">${inviteUrl}</a>
</p>

<%include file="_footer.mako"/>
