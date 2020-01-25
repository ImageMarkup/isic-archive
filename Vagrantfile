# Vagrant > 1.8.1 is required due to
# https://github.com/mitchellh/vagrant/issues/6793
Vagrant.require_version '>= 1.8.3'

def true?(obj)
  obj = obj.to_s.downcase
  obj != 'false' && obj != 'off' && obj != '0'
end

Vagrant.configure('2') do |config|
    config.vm.box = 'bento/ubuntu-18.04'
    config.vm.hostname = 'isic-archive.test'
    config.vm.provider 'virtualbox' do |virtualbox|
      virtualbox.name = 'isic-archive.test'
      virtualbox.memory = 2048
    end

    config.vm.network :private_network, ip: '172.16.0.10'
    config.vm.post_up_message = <<-EOS
  ISIC Archive is running at http://isic-archive.test/admin
  MailHog is running at http://isic-archive.test:8025/mailhog/
  S3 (via minio) is running at http://isic-archive.test:9000
    EOS

    config.vm.synced_folder '.', '/vagrant', disabled: true
    config.vm.synced_folder '.', '/home/vagrant/isic_archive'

    config.vm.provision 'ansible_local' do |ansible|
      ansible.provisioning_path = '/home/vagrant/isic_archive/ansible'
      ansible.galaxy_role_file = 'requirements.yml'
      ansible.playbook = 'vagrant-playbook.yml'
    end

    config.ssh.forward_agent = true
    config.ssh.forward_x11 = true
end
