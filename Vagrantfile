# Vagrant > 1.8.1 is required due to
# https://github.com/mitchellh/vagrant/issues/6793
Vagrant.require_version '>= 1.8.3'

def true?(obj)
  obj = obj.to_s.downcase
  obj != 'false' && obj != 'off' && obj != '0'
end

Vagrant.configure('2') do |config|
  config.vm.define 'web' do |web|
    web.vm.box = 'bento/ubuntu-18.04'
    web.vm.hostname = 'isic-archive.test'
    web.vm.provider 'virtualbox' do |virtualbox|
      virtualbox.name = 'isic-archive.test'
      virtualbox.memory = 2048
    end

    web.vm.network :private_network, ip: '172.16.0.10'
    web.vm.post_up_message = <<-EOS
  ISIC Archive is running at http://isic-archive.test/admin
  MailHog is running at http://isic-archive.test:8025
  Flower is running at http://isic-archive.test:5555
  S3 (via minio) is running at http://isic-archive.test:9000
    EOS

    web.vm.synced_folder '.', '/vagrant', disabled: true
    web.vm.synced_folder '.', '/home/vagrant/isic_archive'

    web.vm.provision 'ansible_local' do |ansible|
      ansible.provisioning_path = '/home/vagrant/isic_archive/ansible'
      ansible.galaxy_role_file = 'requirements.yml'
      ansible.playbook = 'vagrant-webservers.yml'
      ansible.extra_vars = {
        isic_archive_editable: true,
        webserver_ip: '172.16.0.10',
        broker_ip: '172.16.0.11'
      }
    end

    web.ssh.forward_agent = true
    web.ssh.forward_x11 = true
  end

  config.vm.define 'worker' do |worker|
    worker.vm.box = 'bento/ubuntu-18.04'
    worker.vm.hostname = 'worker.isic-archive.test'
    worker.vm.provider 'virtualbox' do |virtualbox|
      virtualbox.name = 'worker.isic-archive.test'
      virtualbox.memory = 2048
    end

    worker.vm.network :private_network, ip: '172.16.0.11'

    worker.vm.synced_folder '.', '/vagrant', disabled: true
    worker.vm.synced_folder '.', '/home/vagrant/isic_archive'

    worker.vm.provision 'ansible_local' do |ansible|
      ansible.provisioning_path = '/home/vagrant/isic_archive/ansible'
      ansible.galaxy_role_file = 'requirements.yml'
      ansible.playbook = 'vagrant-brokers.yml'
      ansible.extra_vars = {
        webserver_ip: '172.16.0.10',
        broker_ip: '172.16.0.11'
      }
    end

    worker.vm.provision 'ansible_local' do |ansible|
      ansible.provisioning_path = '/home/vagrant/isic_archive/ansible'
      ansible.galaxy_role_file = 'requirements.yml'
      ansible.playbook = 'vagrant-workers.yml'
      ansible.extra_vars = {
        webserver_ip: '172.16.0.10',
        broker_ip: '172.16.0.11'
      }
    end

    worker.ssh.forward_agent = true
    worker.ssh.forward_x11 = true
  end
end
