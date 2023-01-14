{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";

  outputs = { self, nixpkgs, flake-utils }:
    {
      nixosModules.default = import ./nixos-module.nix;  
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        py = pkgs.python310Packages;

        idlez = py.buildPythonPackage {
          pname = "idlez";
          version = "0.0.1";
          src = ./.;

          propagatedBuildInputs = with py; [ discordpy ];

          checkInputs = with py; [ pytest pytestcov mypy ];
          checkPhase = ''
            runHook preCheck
            pytest
            mypy -p idlez
            runHook postCheck
          '';
          doCheck = false;
        };
      in {
        packages = {
          inherit idlez;
          default = idlez;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ idlez ];
          buildInputs = with pkgs; [
            black
            py.pytest
            py.pytestcov
            py.mypy
          ];
        };
      });
}
