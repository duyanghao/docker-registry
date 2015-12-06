%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# removed "|| 0%{?rhel} >= 7" as the rhel version is maintained separately
%if 0%{?fedora} >= 19
%bcond_without  systemd
%endif

Summary:    Registry server for Docker
Name:       docker-registry
Version:    0.9.2
Release:    1%{?dist}
License:    ASL 2.0
URL:        https://github.com/TencentSA/%{name}
Source:     https://github.com/TencentSA/%{name}/archive/%{version}.tar.gz
Source1:    %{name}.service
Source2:    %{name}.sysconfig
Source3:    %{name}.sysvinit

BuildRequires:      python2-devel
%if %{with systemd}
BuildRequires:      systemd
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%else
Requires(post):     chkconfig
Requires(preun):    chkconfig
Requires(postun):   initscripts
Requires:           python-importlib
%endif

Requires:   python-redis
Requires:   python-boto
Requires:   PyYAML
Requires:   python-argparse
Requires:   python-backports-lzma
Requires:   python-blinker
#Requires:   python-docker-registry-core >= 2.0.1-2
Requires:   python-flask
Requires:   python-gevent
Requires:   python-gunicorn
Requires:   python-jinja2
Requires:   python-requests
Requires:   python-rsa
Requires:   python-simplejson
Requires:   python-sqlalchemy
BuildArch:  noarch

%description
Registry server for Docker (hosting/delivering of repositories and images).

%prep
%setup -qn %{name}-%{version}

# Remove the golang implementation
# It's not the main one (yet?)
rm -rf contrib/golang_impl
find . -name "*.py" \
         -print |\
         xargs sed -i '/flask_cors/d'

%build
%{__python} setup.py build

%install
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_sharedstatedir}/%{name}
install -d %{buildroot}%{python_sitelib}/%{name}

install -pm 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}

%if %{with systemd}
install -d %{buildroot}%{_unitdir}
install -pm 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
# Make sure we set proper WorkingDir in the systemd service file
sed -i "s|#WORKDIR#|%{python_sitelib}/%{name}|" %{buildroot}%{_unitdir}/%{name}.service
%else
install -d %{buildroot}%{_initddir}
install -pm 755 %{SOURCE3} %{buildroot}%{_initddir}/%{name}
# Make sure we set proper working dir in the sysvinit file
sed -i "s|#WORKDIR#|%{python_sitelib}/%{name}|" %{buildroot}%{_initddir}/%{name}
%endif

cp -pr docker_registry tests %{buildroot}%{python_sitelib}/%{name}
cp config/config_sample.yml %{buildroot}%{_sysconfdir}/%{name}.yml
sed -i 's/\/tmp\/registry/\/var\/lib\/docker-registry/g' %{buildroot}%{_sysconfdir}/%{name}.yml
cp -r depends/docker-registry-core/docker_registry/* %{buildroot}%{python_sitelib}/%{name}/docker_registry/

%post
%if %{with systemd}
%systemd_post %{name}.service
%else
/sbin/chkconfig --add %{name}
%endif

%preun
%if %{with systemd}
%systemd_preun %{name}.service
%else
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if %{with systemd}
%systemd_postun_with_restart %{name}.service
%else
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
%endif

%files
%doc AUTHORS CHANGELOG.md LICENSE README.md
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.yml
%dir %{python_sitelib}/%{name}
%{python_sitelib}/%{name}/*
%dir %{_sharedstatedir}/%{name}
%if %{with systemd}
%{_unitdir}/%{name}.service
%else
%{_initddir}/%{name}
%endif

%changelog
* Wed Nov 26 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.9.0-1
- Resolves: rhbz#1163120 - update to upstream v0.9.0

* Fri Sep 05 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.8.1-2
- Resolves: rhbz#1137026 - remove flask_cors (not packaged yet)
- Package owns all dirs created
- update runtime requirements

* Tue Sep 02 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.8.1-1
- Resolves: rhbz#1130008 - upstream release 0.8.1

* Mon Aug 11 2014 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.7.3-1
- Resolves: rhbz#1111813 - upstream release 0.7.3
- Resolves: rhbz#1120214 - unitfile doesn't use redis.service

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Jun 05 2014 Marek Goldmann <mgoldman@redhat.com> - 0.7.1-2
- Require python-importlib for EPEL 6

* Thu Jun 05 2014 Marek Goldmann <mgoldman@redhat.com> - 0.7.1-1
- Upstream release 0.7.1

* Fri Apr 18 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.8-1
- Upstream release 0.6.8

* Mon Apr 07 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.6-2
- docker-registry settings in /etc/sysconfig/docker-registry not honored,
  RHBZ#1072523

* Thu Mar 20 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.6-1
- Upstream release 0.6.6
- docker-registry cannot import module jinja2, RHBZ#1077630

* Mon Feb 17 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.5-1
- Upstream release 0.6.5

* Tue Jan 07 2014 Marek Goldmann <mgoldman@redhat.com> - 0.6.3-1
- Upstream release 0.6.3
- Added python-backports-lzma and python-rsa to R
- Removed configuration file path patch, it's in upstream

* Fri Dec 06 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-4
- Docker-registry does not currently support moving the config file, RHBZ#1038874

* Mon Dec 02 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-3
- EPEL support
- Comments in the sysconfig/docker-registry file

* Wed Nov 27 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-2
- Added license and readme

* Wed Nov 20 2013 Marek Goldmann <mgoldman@redhat.com> - 0.6.0-1
- Initial packaging

