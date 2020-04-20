<%include file="_header.mako"/>

<p>
Dear <b>${user['firstName']} ${user['lastName']}</b>,
</p>

<p>
% if not errors and warnings:
Your application of metadata to ${dataset['name']} succeeded, with warnings.
% elif not warnings:
Your application of metadata to ${dataset['name']} succeeded.
% else:
Your application of metadata to ${dataset['name']} failed for the reasons below.
% endif

% if warnings:
    <h4>Warnings</h4>
    % for warning in warnings:
        ${warning}<br>
    % endfor
% endif
<br />
<br />
% if errors:
    <h4>Errors</h4>
    % for error in errors:
        ${error}<br>
    % endfor
% endif
</p>

<%include file="_footer.mako"/>
