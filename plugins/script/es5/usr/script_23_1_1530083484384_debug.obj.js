function cmsapp(argv)
{
	argv.$abort("test abort");
	return;
}
module.exports = cmsapp;