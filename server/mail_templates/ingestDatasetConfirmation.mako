<%include file="_header.mako"/>

% if group:
<%include file="ingestDatasetConfirmationHeaderGroup.mako"/>
% else:
<%include file="ingestDatasetConfirmationHeaderUser.mako"/>
% endif

<%include file="ingestDatasetConfirmationTable.mako"/>

% if not group:
<p>
The Terms of Use that you agreed to via electronic signature is available here:<br>
<a href="${host}#termsOfUse">${host}#termsOfUse</a>
</p>
% endif

<%include file="_footer.mako"/>
