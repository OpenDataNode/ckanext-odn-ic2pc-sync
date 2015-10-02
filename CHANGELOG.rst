---------
Changelog
---------

v1.2.1 2015-10-02

Bug fixes:
 * Fixed bug when updating datastore resource

v1.2.0 2015-09-23

Notes:
 * Version jumped to 1.2.0 in order to align with tags / ODN releases

New Features:
 * Added option to create dataset as private in external catalog, when synchronizing for the first time

Bug fixes:
 * QueuePool limit overflow fixed when starting automatic synchronization

v0.6.2 2015-08-05

Bug fixes:
 * fixed inability to verify and add external catalog with user api key that has only editor rights in organization

v0.6.1 2015-07-29

Bug fixes:
 * multiprocessing: synchronization error if package_create and package_update are called in fast succession
 * not localized strings
 * inability to synchronize resource with diacritics in name

v0.6.0 2015-06-23

New Features:
 * Added complex verification for external catalog

Bug fixes:
 * None