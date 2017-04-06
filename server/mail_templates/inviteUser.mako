<%include file="_header.mako"/>

<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
Greetings ${newUser['firstName']} ${newUser['lastName']},<br>
You have been invited to use the ISIC Archive.
</div>

<p>
Please use the following link to finalize your account:<br>
<a href="${inviteUrl}">${inviteUrl}</a>
</p>

<%include file="_footer.mako"/>
