About this folder
=================

There's some strange voodoo going on in here. For example, to use this code with mongodb's mapreduce engine, the map and reduce script strings must contain exactly one function, and there is no way to pass any additional parameters. We get around this by using python to wrap code like this:

```
function map () {
  var params = {... stringified parameter object ...};

  ... embedded code ...

}
```

There are also complications because mongodb can't return an array, so you will see seemingly unnecessary wrapping up of arrays in objects. For example, we append this kind of return statement to the reduce function:

```
return {histogram: histogram};
```
