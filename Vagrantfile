# Vagrant > 1.8.1 is required due to
# https://github.com/mitchellh/vagrant/issues/6793
Vagrant.require_version ">= 1.8.3"

def true?(obj)
  obj = obj.to_s.downcase
  obj != "false" && obj != "off" && obj != "0"
end

Vagrant.configure("2") do |config|
  bind_node_modules = true?(ENV.fetch("BIND_NODE_MODULES", Vagrant::Util::Platform.windows?))

  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "isic-archive.devel"
  config.vm.provider "virtualbox" do |virtualbox|
    virtualbox.name = "isic-archive.devel"
    virtualbox.memory = 2048
  end

  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.post_up_message = "ISIC Archive is running at http://localhost:8080"

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/vagrant/isic_archive"

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "ansible/vagrant-playbook.yml"
    ansible.galaxy_role_file = "ansible/requirements.yml"
    ansible.provisioning_path = "/home/vagrant/isic_archive"
    ansible.extra_vars = {
      bind_node_modules: bind_node_modules
    }
  end

  config.ssh.forward_agent = true
  config.ssh.forward_x11 = true
end
