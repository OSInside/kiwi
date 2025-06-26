from kiwi.builder.template.container_import import BuilderTemplateSystemdUnit


class TestBuilderTemplateSystemdUnit:
    def setup_method(self):
        self.template = BuilderTemplateSystemdUnit()

    def test_get_container_import_template_with_container_snap_service(self):
        container_files = ['/var/tmp/kiwi_containers/test-app_v1.0']
        load_commands = [['/usr/bin/container-snap', 'load', '-i', '/var/tmp/kiwi_containers/test-app_v1.0']]
        after_services = ['container-snap.service']

        template = self.template.get_container_import_template(
            container_files, load_commands, after_services
        )

        unit_content = template.substitute()

        expected_unit = """# kiwi generated unit file
[Unit]
Description=Import Local Container(s)
ConditionPathExists=/var/tmp/kiwi_containers/test-app_v1.0
After=container-snap.service
[Service]
Type=oneshot
ExecStart=/usr/bin/container-snap load -i /var/tmp/kiwi_containers/test-app_v1.0
ExecStartPost=/bin/rm -f /var/tmp/kiwi_containers/test-app_v1.0
[Install]
WantedBy=multi-user.target
"""

        assert unit_content == expected_unit

    def test_get_container_import_template_with_multiple_services(self):
        container_files = [
            '/var/tmp/kiwi_containers/app1_latest',
            '/var/tmp/kiwi_containers/app2_v1.0'
        ]
        load_commands = [
            ['/usr/bin/docker', 'load', '-i', '/var/tmp/kiwi_containers/app1_latest'],
            ['/usr/bin/container-snap', 'load', '-i', '/var/tmp/kiwi_containers/app2_v1.0']
        ]
        after_services = ['docker.service', 'container-snap.service']

        template = self.template.get_container_import_template(
            container_files, load_commands, after_services
        )

        unit_content = template.substitute()

        expected_unit = """# kiwi generated unit file
[Unit]
Description=Import Local Container(s)
ConditionPathExists=/var/tmp/kiwi_containers/app1_latest
ConditionPathExists=/var/tmp/kiwi_containers/app2_v1.0
After=docker.service container-snap.service
[Service]
Type=oneshot
ExecStart=/usr/bin/docker load -i /var/tmp/kiwi_containers/app1_latest
ExecStart=/usr/bin/container-snap load -i /var/tmp/kiwi_containers/app2_v1.0
ExecStartPost=/bin/rm -f /var/tmp/kiwi_containers/app1_latest
ExecStartPost=/bin/rm -f /var/tmp/kiwi_containers/app2_v1.0
[Install]
WantedBy=multi-user.target
"""

        assert unit_content == expected_unit

    def test_get_container_import_template_no_after_services(self):
        container_files = ['/var/tmp/kiwi_containers/test-app_latest']
        load_commands = [['/usr/bin/podman', 'load', '-i', '/var/tmp/kiwi_containers/test-app_latest']]
        after_services = []

        template = self.template.get_container_import_template(
            container_files, load_commands, after_services
        )

        unit_content = template.substitute()

        expected_unit = """# kiwi generated unit file
[Unit]
Description=Import Local Container(s)
ConditionPathExists=/var/tmp/kiwi_containers/test-app_latest
[Service]
Type=oneshot
ExecStart=/usr/bin/podman load -i /var/tmp/kiwi_containers/test-app_latest
ExecStartPost=/bin/rm -f /var/tmp/kiwi_containers/test-app_latest
[Install]
WantedBy=multi-user.target
"""

        assert unit_content == expected_unit

    def test_get_container_import_template_empty_inputs(self):
        template = self.template.get_container_import_template([], [], [])

        unit_content = template.substitute()

        expected_unit = """# kiwi generated unit file
[Unit]
Description=Import Local Container(s)
[Service]
Type=oneshot
[Install]
WantedBy=multi-user.target
"""

        assert unit_content == expected_unit
