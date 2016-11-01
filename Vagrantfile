# Required for Ansible Galaxy
Vagrant.require_version ">=1.8.0"

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.hostname = "isic-archive.devel"

  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.post_up_message = "Web server is running at http://127.0.0.1:8080"

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/vagrant/isic_archive"

  provisioner_type = if
      Gem::Version.new(Vagrant::VERSION) > Gem::Version.new('1.8.1')
    then
      # Vagrant > 1.8.1 is required due to
      # https://github.com/mitchellh/vagrant/issues/6793
      "ansible_local"
    else
      "ansible"
    end
  config.vm.provision provisioner_type do |ansible|
    ansible.playbook = "ansible/vagrant-playbook.yml"
    ansible.galaxy_role_file = "ansible/requirements.yml"
    # Ansible has a bug where the "--module-path" option is not respected
    # ansible.raw_arguments = ["--module-path=" + File.expand_path("ansible/library")]
    ENV["ANSIBLE_LIBRARY"] = File.expand_path("ansible/library")
    if provisioner_type == "ansible_local"
      ansible.provisioning_path = "/home/vagrant/isic_archive"
    end
  end

  config.vm.provider "virtualbox" do |virtualbox|
    virtualbox.name = "isic-archive.devel"
    virtualbox.memory = 1536
  end

  config.ssh.forward_agent = true
  config.ssh.forward_x11 = true
end
