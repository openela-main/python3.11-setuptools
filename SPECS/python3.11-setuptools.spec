%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11

%global srcname setuptools

# Some dependencies are missing on RHEL
%bcond_with tests

#  WARNING  When bootstrapping, disable tests as well,
#           because tests need pip.
%bcond_with bootstrap
# Similar to what we have in pythonX.Y.spec files.
# If enabled, provides unversioned executables and other stuff.


%if %{without bootstrap}
%global python_wheel_name %{srcname}-%{version}-py3-none-any.whl
%global python3_record %{python3_sitelib}/%{srcname}-%{version}.dist-info/RECORD
%endif

Name:           python%{python3_pkgversion}-setuptools
# When updating, update the bundled libraries versions bellow!
Version:        65.5.1
Release:        2%{?dist}
Summary:        Easily build and distribute Python packages
# setuptools is MIT
# appdirs is MIT
# more-itertools is MIT
# ordered-set is MIT
# packaging is BSD or ASL 2.0
# pyparsing is MIT
# importlib-metadata is ASL 2.0
# importlib-resources is ASL 2.0
# jaraco.text is MIT
# typing-extensions is Python
# zipp is MIT
# nspektr is MIT
# tomli is MIT
# the setuptools logo is MIT
License:        MIT and ASL 2.0 and (BSD or ASL 2.0) and Python
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        %{pypi_source %{srcname} %{version}}

# Some test deps are optional and either not desired or not available in Fedora, thus this patch removes them.
Patch0:          Remove-optional-or-unpackaged-test-deps.patch

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-rpm-macros
%if %{with tests}
BuildRequires:  gcc
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-xdist
BuildRequires:  python%{python3_pkgversion}-pytest-virtualenv
BuildRequires:  python%{python3_pkgversion}-jaraco-envs
BuildRequires:  python%{python3_pkgversion}-jaraco-path
BuildRequires:  python%{python3_pkgversion}-virtualenv
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  python%{python3_pkgversion}-build
BuildRequires:  python%{python3_pkgversion}-ini2toml
BuildRequires:  python%{python3_pkgversion}-tomli-w
%endif # with tests
%if %{without bootstrap}
# Not to use the pre-generated egg-info, we use setuptools from previous build to generate it
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  python%{python3_pkgversion}-setuptools
# python3 bootstrap: this is built before the final build of python3, which
# adds the dependency on python3-rpm-generators, so we require it manually
BuildRequires:  python3-rpm-generators
%endif # without bootstrap

# Virtual provides for the packages bundled by setuptools.
# Bundled packages are defined in two files:
# - pkg_resources/_vendor/vendored.txt, and
# - setuptools/_vendor/vendored.txt
# Merge them to one and then generate the list with:
# %%{_rpmconfigdir}/pythonbundles.py --namespace 'python%%{python3_pkgversion}dist' allvendor.txt
%global bundled %{expand:
Provides: bundled(python%{python3_pkgversion}dist(appdirs)) = 1.4.3
Provides: bundled(python%{python3_pkgversion}dist(importlib-metadata)) = 4.11.1
Provides: bundled(python%{python3_pkgversion}dist(importlib-resources)) = 5.4
Provides: bundled(python%{python3_pkgversion}dist(jaraco-text)) = 3.7
Provides: bundled(python%{python3_pkgversion}dist(more-itertools)) = 8.8
Provides: bundled(python%{python3_pkgversion}dist(ordered-set)) = 3.1.1
Provides: bundled(python%{python3_pkgversion}dist(packaging)) = 21.3
Provides: bundled(python%{python3_pkgversion}dist(pyparsing)) = 3.0.9
Provides: bundled(python%{python3_pkgversion}dist(typing-extensions)) = 4.0.1
Provides: bundled(python%{python3_pkgversion}dist(zipp)) = 3.7
Provides: bundled(python%{python3_pkgversion}dist(tomli)) = 2.0.1
}

%{bundled}

# For users who might see ModuleNotFoundError: No module named 'pkg_resources'
# NB: Those are two different provides: one contains underscore, the other hyphen
%py_provides    python%{python3_pkgversion}-pkg_resources
%py_provides    python%{python3_pkgversion}-pkg-resources

%description
Setuptools is a collection of enhancements to the Python 3 distutils that allow
you to more easily build and distribute Python 3 packages, especially ones that
have dependencies on other packages.

This package also contains the runtime components of setuptools, necessary to
execute the software that requires pkg_resources.

%if %{without bootstrap}
%package -n     %{python_wheel_pkg_prefix}-%{srcname}-wheel
Summary:        The setuptools wheel
%{bundled}

%description -n %{python_wheel_pkg_prefix}-%{srcname}-wheel
A Python wheel of setuptools to use with venv.
%endif


%prep
%autosetup -p1 -n %{srcname}-%{version}
%if %{without bootstrap}
# If we don't have setuptools installed yet, we use the pre-generated .egg-info
# See https://github.com/pypa/setuptools/pull/2543
# And https://github.com/pypa/setuptools/issues/2550
# WARNING: We cannot remove this folder since Python 3.11.1,
#          see https://github.com/pypa/setuptools/issues/3761
#rm -r %%{srcname}.egg-info
%endif

# Strip shbang
find setuptools pkg_resources -name \*.py | xargs sed -i -e '1 {/^#!\//d}'
# Remove bundled exes
rm -f setuptools/*.exe
# Don't ship these
rm -r docs/conf.py


%build
%if %{without bootstrap}
%py3_build_wheel
%else
%py3_build
%endif


%install
%if %{without bootstrap}
%py3_install_wheel %{python_wheel_name}
%else
%py3_install
%endif

# https://github.com/pypa/setuptools/issues/2709
rm -rf %{buildroot}%{python3_sitelib}/pkg_resources/tests/

%if %{without bootstrap}
sed -i '/^setuptools\/tests\//d' %{buildroot}%{python3_record}
%endif

find %{buildroot}%{python3_sitelib} -name '*.exe' | xargs rm -f

%if %{without bootstrap}
mkdir -p %{buildroot}%{python_wheel_dir}
install -p dist/%{python_wheel_name} -t %{buildroot}%{python_wheel_dir}
%endif

%check

# Regression tests

#%%if 0%{?rhel} >= 9
# The test cannot run on RHEL8 due to the test script missing from RPM.
# Verify bundled provides are up to date
# Disable the test for now as it requires python3-setuptools which is not included in the
# minimal set of packages.
#cat pkg_resources/_vendor/vendored.txt setuptools/_vendor/vendored.txt > allvendor.txt
#%%{_rpmconfigdir}/pythonbundles.py allvendor.txt --namespace 'python%{python3_pkgversion}dist' --compare-with '%%{bundled}'
#%%endif

%if %{without bootstrap}
# Regression test, the wheel should not be larger than 900 kB
# https://bugzilla.redhat.com/show_bug.cgi?id=1914481#c3
test $(stat --format %%s dist/%{python_wheel_name}) -lt 900000
%endif

# Regression test, the tests are not supposed to be installed
test ! -d %{buildroot}%{python3_sitelib}/pkg_resources/tests
test ! -d %{buildroot}%{python3_sitelib}/setuptools/tests

# https://github.com/pypa/setuptools/discussions/2607
rm pyproject.toml

# Upstream test suite

%if %{with tests}
# Upstream tests
# --ignore=setuptools/tests/test_integration.py
# --ignore=setuptools/tests/integration/
# --ignore=setuptools/tests/config/test_apply_pyprojecttoml.py
# -k "not test_pip_upgrade_from_source"
#   the tests require internet connection
# --ignore=setuptools/tests/test_editable_install.py
#   the tests require pip-run which we don't have in Fedora
PRE_BUILT_SETUPTOOLS_WHEEL=dist/%{python_wheel_name} \
PYTHONPATH=$(pwd) %pytest \
 --ignore=setuptools/tests/test_integration.py \
 --ignore=setuptools/tests/integration/ \
 --ignore=setuptools/tests/test_editable_install.py \
 --ignore=setuptools/tests/config/test_apply_pyprojecttoml.py \
 -k "not test_pip_upgrade_from_source"
%endif # with tests


%files -n python%{python3_pkgversion}-setuptools
%license LICENSE
%doc docs/* CHANGES.rst README.rst
%{python3_sitelib}/distutils-precedence.pth
%{python3_sitelib}/pkg_resources/
%{python3_sitelib}/setuptools*/
%{python3_sitelib}/_distutils_hack/

%if %{without bootstrap}
%files -n %{python_wheel_pkg_prefix}-%{srcname}-wheel
%license LICENSE
# we own the dir for simplicity
%dir %{python_wheel_dir}/
%{python_wheel_dir}/%{python_wheel_name}
%endif


%changelog
* Mon Jan 30 2023 Charalampos Stratakis <cstratak@redhat.com> - 65.5.1-2
- Disable bootstrap

* Wed Oct 12 2022 Charalampos Stratakis <cstratak@redhat.com> - 65.5.1-1
- Initial package
- Fedora contributions by:
      # Bill Nottingham <notting@fedoraproject.org>
      # Charalampos Stratakis <cstratak@redhat.com>
      # David Malcolm <dmalcolm@redhat.com>
      # Dennis Gilmore <dennis@ausil.us>
      # dmalcolm <dmalcolm@fedoraproject.org>
      # Haikel Guemar <hguemar@fedoraproject.org>
      # Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>
      # Jesse Keating <jkeating@fedoraproject.org>
      # Karolina Surma <ksurma@redhat.com>
      # Kevin Fenzi <kevin@scrye.com>
      # Konstantin Ryabitsev <icon@fedoraproject.org>
      # Lumir Balhar <lbalhar@redhat.com>
      # Matej Stuchlik <mstuchli@redhat.com>
      # Michal Cyprian <mcyprian@redhat.com>
      # Miro Hrončok <miro@hroncok.cz>
      # Nils Philippsen <nils@redhat.com>
      # Orion Poplawski <orion@cora.nwra.com>
      # Petr Viktorin <pviktori@redhat.com>
      # Pierre-Yves Chibon <pingou@pingoured.fr>
      # Ralph Bean <rbean@redhat.com>
      # Randy Barlow <randy@electronsweatshop.com>
      # Robert Kuska <rkuska@redhat.com>
      # Thomas Spura <thomas.spura@gmail.com>
      # Tomáš Hrnčiar <thrnciar@redhat.com>
      # Tomas Orsava <torsava@redhat.com>
      # Tomas Radej <tradej@redhat.com>
      # tomspur <tomspur@fedoraproject.org>
      # Toshio Kuratomi <toshio@fedoraproject.org>
      # Troy Dawson <tdawson@redhat.com>
      # Ville Skyttä <scop@fedoraproject.org>
