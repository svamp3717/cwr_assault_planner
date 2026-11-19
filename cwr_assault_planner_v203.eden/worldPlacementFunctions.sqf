// CWA/OFP placement helpers, loaded after worldConfig.sqs on every machine.
// [x,y,z,margin] -> bounded position; cap margin to half the shorter axis.
worldClampPosition = {
    private ["_x","_y","_z","_margin","_halfX","_halfY"];
    _x = _this select 0;
    _y = _this select 1;
    _z = _this select 2;
    _margin = _this select 3;
    _halfX = (worldMaxX - worldMinX) / 2;
    _halfY = (worldMaxY - worldMinY) / 2;
    if (_margin > _halfX) then {_margin = _halfX};
    if (_margin > _halfY) then {_margin = _halfY};
    if (_x < worldMinX + _margin) then {_x = worldMinX + _margin};
    if (_x > worldMaxX - _margin) then {_x = worldMaxX - _margin};
    if (_y < worldMinY + _margin) then {_y = worldMinY + _margin};
    if (_y > worldMaxY - _margin) then {_y = worldMaxY - _margin};
    [_x,_y,_z]
};

// [x,y,dx,dy,z,margin] -> offset, reflecting an axis only when it improves
// available distance and the requested point would be clipped.
worldOffsetPosition = {
    private ["_x","_y","_dx","_dy","_z","_margin","_pos","_alt"];
    _x = _this select 0;
    _y = _this select 1;
    _dx = _this select 2;
    _dy = _this select 3;
    _z = _this select 4;
    _margin = _this select 5;
    _pos = [_x + _dx,_y + _dy,_z,_margin] call worldClampPosition;
    _alt = [_x - _dx,_y - _dy,_z,_margin] call worldClampPosition;
    if (abs ((_pos select 0) - _x) < abs ((_alt select 0) - _x)) then {_dx = -_dx};
    if (abs ((_pos select 1) - _y) < abs ((_alt select 1) - _y)) then {_dy = -_dy};
    [_x + _dx,_y + _dy,_z,_margin] call worldClampPosition
};

// [dx,dy,z] relative to setup base. Fit the legacy layout as a whole,
// preserving spacing instead of stacking all units on a map boundary.
worldSetupPosition = {
    private ["_dx","_dy","_z","_scale","_scaleX","_scaleY","_ax","_ay"];
    _dx = _this select 0;
    _dy = _this select 1;
    _z = _this select 2;
    _scale = 1;
    _scaleX = (worldMaxX - worldMinX) / 640;
    _scaleY = (worldMaxY - worldMinY) / 850;
    if (_scale > _scaleX) then {_scale = _scaleX};
    if (_scale > _scaleY) then {_scale = _scaleY};
    _ax = missionBaseX;
    _ay = missionBaseY;
    if (_ax < worldMinX + 150 * _scale) then {_ax = worldMinX + 150 * _scale};
    if (_ax > worldMaxX - 490 * _scale) then {_ax = worldMaxX - 490 * _scale};
    if (_ay < worldMinY + 810 * _scale) then {_ay = worldMinY + 810 * _scale};
    if (_ay > worldMaxY - 40 * _scale) then {_ay = worldMaxY - 40 * _scale};
    [_ax + _dx * _scale,_ay + _dy * _scale,_z]
};
