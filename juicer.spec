%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
%endif

Name: juicer
Release: 1%{?dist}
Summary: Pulp and release carts
Version: 0.0.1

Group: Development/Libraries
License: GPLv3+
Source0: https://docspace.corp.redhat.com/docs/DOC-104668/%{name}-%{version}.tar.gz
Url: https://docspace.corp.redhat.com/docs/DOC-104668

BuildArch: noarch
BuildRequires: python2-devel

Requires: python-requests >= 0.13.1


%description
Pulp stuff, oh -- and release carts.


%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT
# system configs?
#mkdir -p $RPM_BUILD_ROOT/etc/juicer/
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1/
cp -v docs/man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
# usr/share/juicer/ --> examples?
#mkdir -p $RPM_BUILD_ROOT/%{_datadir}/juicer
#cp -v library/* $RPM_BUILD_ROOT/%{_datadir}/juicer/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/juicer*
%{_bindir}/juicer*
#%{_datadir}/juicer
#%config(noreplace) %{_sysconfdir}/juicer
%doc README PKG-INFO
%doc %{_mandir}/man1/juicer*
%doc %{_mandir}/man5/juicer*


%changelog
* Mon Jun 18 2012 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-1
- First release

