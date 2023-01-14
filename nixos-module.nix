{ config, pkgs, lib, ... }: 

with lib; 

let
  cfg = config.services.idlez;
in {
  options.services.idlez = {
    enable = mkEnableOption "Enable idlez bot";

    dataDir = mkOption {
      type = types.singleLineStr;
      description = ''Data directory'';
      default = "/var/lib/idlez";
    };

    tokenFile = mkOption {
      type = types.singleLineStr;
      description = ''File that contains the token string'';
      default = "/private/idlez.token";
    };
  };

  config = mkIf cfg.enable {
    users.users.idlez = {
      isSystemUser = true;
      group = "idlez";
      home = mkDefault cfg.dataDir;
      createHome = mkDefault true;
    };
    users.groups.idlez = {};

    systemd.services.idlez = {
      enable = true;

      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      path = [ pkgs.idlez ];

      description = "idlez bot";
      preStart = ''
        if ! test -e ${cfg.dataDir}; then
          mkdir -p ${cfg.dataDir}
        fi
      '';

      serviceConfig = {
        User = "idlez";
        Group = "idlez";
        ExecStart = "${pkgs.idlez}/bin/idlez --token-file=${cfg.tokenFile} --data-dir=${cfg.dataDir}";
        Restart = "always";
        RestartSec = 30;
        RuntimeDirectory = "idlez";
        RuntimeDirectoryMode = "0750";
      };
      unitConfig = {
        RequiresMountsFor = cfg.dataDir;
      };
    };
  };
}