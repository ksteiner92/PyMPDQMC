module dqmc
    use dqmc_cfg
    use dqmc_geom_wrap
    use dqmc_hubbard
    use dqmc_mpi
    use dqmc_tdm1

    implicit none

    type(Hubbard)       :: Hub
    type(config)        :: cfg
    type(GeomWrap)      :: Gwrap
    integer             :: symmetries_output_file_unit
    integer             :: nmu

    interface setParameter
        module procedure setParameterI, setParameterR
        module procedure setParameterS, setParameterPR
        module procedure setParameterPI
    end interface

    !interface getParameter
    !    module procedure getParameterI, getParameterR
    !    module procedure getParameterS, getParameterPR
    !    module procedure getParameterPI
    !end interface

contains

function getParameterI(name) result(value)
    character(len=*) :: name
    integer       :: value
    call CFG_GET(cfg, name, value)
end

function getParameterR(name) result(value)
    character(len=*) :: name
    real(wp)     :: value
    call CFG_GET(cfg, name, value)
end

subroutine getParameterS(name, value)
    character(len=slen), intent(in)     :: name
    character(len=slen), intent(inout) :: value
    call CFG_GET(cfg, name, value)
end

function getParameterPR(name, n) result(value)
    character(len=*) :: name
    real(wp), pointer :: value(:)
    integer         :: n
    call CFG_GET(cfg, name, n, value)
end

function getParameterPI(name, n) result(value)
    character(len=*) :: name
    integer, pointer :: value(:)
    integer          :: n
    call CFG_GET(cfg, name, n, value)
end

subroutine setParameterI(name, value)
    character(len=*), intent(in) :: name
    integer, intent(in)          :: value
    call CFG_Set(cfg, name, value)
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setParameterR(name, value)
    character(len=*), intent(in) :: name
    real(wp), intent(in)         :: value
    call CFG_Set(cfg, name, value)
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setParameterS(name, value)
    character(*), intent(in)     :: name
    character(*), intent(in)     :: value
    call CFG_Set(cfg, name, value)
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setParameterPR(name, value, n)
    character(len=*), intent(in) :: name
    real(wp), intent(in)         :: value(n)
    integer, intent(in)          :: n
    call CFG_Set(cfg, name, n, value)
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setParameterPI(name, value, n)
    character(len=*), intent(in) :: name
    integer, intent(in)          :: value(n)
    integer, intent(in)          :: n
    call CFG_Set(cfg, name, n, value)
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setUniformMu(mu)
    real(wp), intent(in)         :: mu
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) - Hub%mu_up(1:nmu)))
    call CFG_Set(cfg, "mu_dn", Hub%S%nGroup, (Hub%mu_dn(1:nmu) - Hub%mu_dn(1:nmu)))
    call DQMC_Hub_Config(Hub, cfg)
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) + mu))
    call CFG_Set(cfg, "mu_dn", Hub%S%nGroup, (Hub%mu_dn(1:nmu) + mu))
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setUniformMu_up(mu_up)
    real(wp), intent(in)         :: mu_up
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) - Hub%mu_up(1:nmu)))
    call DQMC_Hub_Config(Hub, cfg)
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) + mu_up))
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setUniformMu_dn(mu_dn)
    real(wp), intent(in)         :: mu_dn
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_dn(1:nmu) - Hub%mu_dn(1:nmu)))
    call DQMC_Hub_Config(Hub, cfg)
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_dn(1:nmu) + mu_dn))
    call DQMC_Hub_Config(Hub, cfg)
end

subroutine setUniformU(U)
    real(wp), intent(in)         :: U
    Hub%U = U
end

subroutine setGeomFile(gfile)
    character(len=slen) :: gfile
    logical             :: tformat

    !Get general geometry input
    call CFG_Get(cfg, "gfile", gfile)

    call DQMC_Geom_Read_Def(Hub%S, gfile, tformat)
    if (.not.tformat) then
        !If free format fill gwrap
        call DQMC_Geom_Fill(Gwrap, gfile, cfg, symmetries_output_file_unit)
        !Transfer info in Hub%S
        call DQMC_Geom_Init(Gwrap, Hub%S, cfg)
    endif

    call DQMC_Hub_Config(Hub, cfg)
end

function init(cfgfile) result(res)
    character(len=256)  :: cfgfile
    character(len=slen) :: gfile
    logical             :: tformat
    logical             :: res
    integer             :: mu_up_id

    res = .FALSE.

    !Read input
    call DQMC_Read_ConfigFile(cfg, cfgfile)

    !Get general geometry input
    call CFG_Get(cfg, "gfile", gfile)

    ! set geom file
    call setGeomFile(gfile)

    if (Hub%nTry >= Gwrap%Lattice%nSites) then
        write(*,*)
        write(*,"('  number of lattice sites =',i5)") Gwrap%Lattice%nSites
        write(*,"('  ntry =',i5)") Hub%nTry
        write(*,*) " Input 'ntry' exceeds the number of lattice sites."
        write(*,*) " Please reset 'ntry' such that it is less than"
        write(*,*) " the number of lattice sites."
        write(*,*) " Program stopped."
        stop
    end if

    mu_up_id = DQMC_Find_Param(cfg, "mu_up")
    nmu = cfg%record(mu_up_id)%ival
    res = .TRUE.

end

subroutine close()
    call DQMC_Hub_Free(Hub)
    call DQMC_Config_Free(cfg)
    close(symmetries_output_file_unit)
end

subroutine writeConfig(fname)
    type(Param),pointer    :: curr
    integer :: i, j
    character(len=256)  :: fname
    integer, parameter  :: OPT = 666
    integer :: n

    open(unit = OPT, file = fname)
    do i = 1, N_Param
        curr => cfg%record(i)
        if (curr%ptype .eq. TYPE_REAL) then
            if (curr%isArray) then
                write(OPT, "(A,X,'=',X)",advance="no") PARAM_NAME(i)
                n = cfg%record(DQMC_Find_Param(cfg, PARAM_NAME(i)))%ival
                do j = 1, n
                    write(OPT, "(F10.5)", advance="no") curr%rptr(j)
                    if (j < n) then
                        write(OPT, "(','X)", advance="no")
                    end if
                end do
                write(OPT, *) ""
            else
                write(OPT, "(A,X,'=',X,F10.5)") PARAM_NAME(i), curr%rval
            end if
        else if (curr%ptype .eq. TYPE_INTEGER) then
            if (curr%isArray) then
                write(OPT, "(A,X,'=',X)",advance="no") PARAM_NAME(i)
                n = cfg%record(DQMC_Find_Param(cfg, PARAM_NAME(i)))%ival
                do j = 1, n
                    write(OPT, "(I10.5,X)", advance="no") curr%iptr(j)
                    if (j < n) then
                        write(OPT, "(','X)", advance="no")
                    end if
                end do
                write(OPT, *) ""
            else
                write(OPT, "(A,X,'=',X,I10)") PARAM_NAME(i), curr%ival
            end if
        else
            write(OPT, "(A,X,'=',X,A)") PARAM_NAME(i), curr%defaultval
        end if
    end do
    close(OPT)
end

function calculateDensity(mu) result(rho)
    real(wp)            :: rho
    real(wp)            :: mu
    integer             :: nBin, nIter, slice, i, j, k, avg
    real(wp)            :: randn(1)
    real(wp)            :: tmp(2,1)
    real(wp)            :: progress
    integer             :: lastprogprint

    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) - Hub%mu_up(1:nmu)))
    call CFG_Set(cfg, "mu_dn", Hub%S%nGroup, (Hub%mu_dn(1:nmu) - Hub%mu_dn(1:nmu)))
    call DQMC_Hub_Config(Hub, cfg)
    call CFG_Set(cfg, "mu_up", Hub%S%nGroup, (Hub%mu_up(1:nmu) + mu))
    call CFG_Set(cfg, "mu_dn", Hub%S%nGroup, (Hub%mu_dn(1:nmu) + mu))
    call DQMC_Hub_Config(Hub, cfg)

    write(*, *) "calculate density for mu = ", mu, " ..."

    rho = 0.0

    ! Warmup sweep
    write(*, *) "doing warmup ..."
    do i = 1, Hub%nWarm
        call DQMC_Hub_Sweep(Hub, NO_MEAS0)
        call DQMC_Hub_Sweep2(Hub, Hub%nTry)
    end do
    ! We divide all the measurement into nBin,
    ! each having nPass/nBin pass.
    nBin   = Hub%P0%nBin
    nIter  = Hub%nPass / Hub%tausk / nBin
    write(*, *) "Starting measuring ..."
    lastprogprint = 0;
    if (nIter > 0) then
        do i = 1, nBin
            do j = 1, nIter
                do k = 1, Hub%tausk
                    call DQMC_Hub_Sweep(Hub, NO_MEAS0)
                    call DQMC_Hub_Sweep2(Hub, Hub%nTry)
                enddo
                ! Fetch a random slice for measurement
                call ran0(1, randn, Hub%seed)
                slice = ceiling(randn(1)*Hub%L)
                call DQMC_Hub_Meas(Hub, slice)
                progress =  real((i - 1) * nIter + j) / real(nIter * nBin) * 100.0;
                if (int(progress) / 10 > lastprogprint) then
                    lastprogprint = int(progress) / 10;
                    write(*,*) (lastprogprint * 10), "%"
                end if
            end do
            ! Accumulate results for each bin
            call DQMC_Phy0_Avg(Hub%P0)
        end do
    endif

    call DQMC_Phy0_GetErr(Hub%P0)
    tmp = Hub%P0%meas(:,Hub%P0%avg:Hub%P0%avg)
    !and here is our density
    rho = (tmp(1, 1) + tmp(2, 1))
end

subroutine run()
    real                :: t1, t2
    type(tdm1)          :: tm
    type(Gtau)          :: tau
    integer             :: na, nt, nkt, nkg, i, j, k, slice, nhist, comp_tdm
    integer             :: nBin, nIter
    character(len=60)   :: ofile
    integer             :: OPT
    integer             :: FLD_UNIT, TDM_UNIT
    real(wp)            :: randn(1)

    call cpu_time(t1)

    !Count the number of processors
    call DQMC_MPI_Init(qmc_sim, PLEVEL_1)

    !Get output file name header
    call CFG_Get(cfg, "ofile", ofile)

    !Save whether to use refinement for G used in measurements.
    call CFG_Get(cfg, "nhist", nhist)

    !if (nhist > 0) then
    !   call DQMC_open_file(adjustl(trim(ofile))//'.HSF.stream','unknown', HSF_output_file_unit)
    !endif

    call DQMC_open_file(adjustl(trim(ofile))//'.geometry','unknown', symmetries_output_file_unit)

    ! Initialize time dependent properties if comp_tdm > 0
    call CFG_Get(cfg, "tdm", comp_tdm)
    if (comp_tdm > 0) then
     call DQMC_open_file(adjustl(trim(ofile))//'.tdm.out','unknown', TDM_UNIT)
     call DQMC_Gtau_Init(Hub, tau)
     call DQMC_TDM1_Init(Hub%L, Hub%dtau, tm, Hub%P0%nbin, Hub%S, Gwrap)
    endif

    ! Warmup sweep
    do i = 1, Hub%nWarm
     if (mod(i, 10)==0) write(*,'(A,i6,1x,i3)')' Warmup Sweep, nwrap  : ', i, Hub%G_up%nwrap
     call DQMC_Hub_Sweep(Hub, NO_MEAS0)
     call DQMC_Hub_Sweep2(Hub, Hub%nTry)
    end do

    ! We divide all the measurement into nBin,
    ! each having nPass/nBin pass.
    nBin   = Hub%P0%nBin
    nIter  = Hub%nPass / Hub%tausk / nBin
    if (nIter > 0) then
     do i = 1, nBin
        do j = 1, nIter
           do k = 1, Hub%tausk
              call DQMC_Hub_Sweep(Hub, NO_MEAS0)
              call DQMC_Hub_Sweep2(Hub, Hub%nTry)
           enddo

           ! Fetch a random slice for measurement
           call ran0(1, randn, Hub%seed)
           slice = ceiling(randn(1)*Hub%L)
           write(*,'(a,3i6)') ' Measurement Sweep, bin, iter, slice : ', i, j, slice

           if (comp_tdm > 0) then
              ! Compute full Green's function
              call DQMC_Gtau_LoadA(tau, TAU_UP, slice, Hub%G_up%sgn)
              call DQMC_Gtau_LoadA(tau, TAU_DN, slice, Hub%G_dn%sgn)
              ! Measure equal-time properties
              call DQMC_Hub_FullMeas(Hub, tau%nnb, tau%A_up, tau%A_dn, tau%sgnup, tau%sgndn)
              ! Measure time-dependent properties
              call DQMC_TDM1_Meas(tm, tau)
           else if (comp_tdm == 0) then
              call DQMC_Hub_Meas(Hub, slice)
           endif

           !Write fields
           !if (nhist > 0) call DQMC_Hub_Output_HSF(Hub, .false., slice, HSF_output_file_unit)
        end do

        ! Accumulate results for each bin
        call DQMC_Phy0_Avg(Hub%P0)
        call DQMC_tdm1_Avg(tm)


        if (Hub%meas2) then
           if(Hub%P2%diagonalize)then
             call DQMC_Phy2_Avg(Hub%P2, Hub%S)
           else
             call DQMC_Phy2_Avg(Hub%P2, Hub%S%W)
           endif
        end if

     end do
    endif

    !Read configurations from file if no sweep was perfomed
    if (Hub%nWarm + Hub%nPass == 0) then
     Hub%nMeas = -1
     call DQMC_count_records(Hub%npass, FLD_UNIT)
     nIter = Hub%npass / nbin
     do i = 1, nBin
        do j = 1, nIter / qmc_sim%aggr_size
           call DQMC_Hub_Input_HSF(Hub, .false., slice, FLD_UNIT)
           call DQMC_Hub_Init_Vmat(Hub)
           if (comp_tdm > 0) then
              ! Compute full Green's function - if fullg is on -
              call DQMC_Gtau_LoadA(tau, TAU_UP, slice, Hub%G_up%sgn)
              call DQMC_Gtau_LoadA(tau, TAU_DN, slice, Hub%G_dn%sgn)
              ! Measure equal-time properties. Pass gtau in case fullg was computed.
              call DQMC_Hub_FullMeas(Hub, tau%nb, &
                 tau%A_up, tau%A_dn, tau%sgnup, tau%sgndn)
              ! Measure time-dependent properties. Reuses fullg when possible.
              call DQMC_TDM1_Meas(tm, tau)
           else if (comp_tdm == 0) then
              call DQMC_Hub_Meas(Hub, slice)
           endif
        enddo
        call DQMC_Phy0_Avg(Hub%P0)
        call DQMC_TDM1_Avg(tm)

        if (Hub%meas2) then
           if(Hub%P2%diagonalize)then
             call DQMC_Phy2_Avg(Hub%P2, Hub%S)
           else
             call DQMC_Phy2_Avg(Hub%P2, Hub%S%W)
           endif
        end if

     enddo
    endif

    !Compute average and error
    call DQMC_Phy0_GetErr(Hub%P0)
    call DQMC_TDM1_GetErr(tm)
    if (Hub%meas2) then
     call DQMC_Phy2_GetErr(Hub%P2)
    end if

    ! Prepare output file
    call DQMC_open_file(adjustl(trim(ofile))//'.out', 'unknown', OPT)

    ! Print computed results
    call DQMC_Hub_OutputParam(Hub, OPT)
    call DQMC_Phy0_Print(Hub%P0, Hub%S, OPT)
    call DQMC_TDM1_Print(tm, TDM_UNIT)

    !Aliases for Fourier transform
    na  =  Gwrap%lattice%natom
    nt  =  Gwrap%lattice%ncell
    nkt =  Gwrap%RecipLattice%nclass_k
    nkg =  Gwrap%GammaLattice%nclass_k

    !Print info on k-points and construct clabel
    call DQMC_Print_HeaderFT(Gwrap, OPT, .true.)
    call DQMC_Print_HeaderFT(Gwrap, OPT, .false.)

    !Compute Fourier transform
    call DQMC_phy0_GetFT(Hub%P0, Hub%S%D, Hub%S%gf_phase, Gwrap%RecipLattice%FourierC, &
       Gwrap%GammaLattice%FourierC, nkt, nkg, na, nt)
    call DQMC_Phy0_GetErrFt(Hub%P0)
    call DQMC_Phy0_PrintFT(Hub%P0, na, nkt, nkg, OPT)

    !Compute Fourier transform and error for TDM's
    call DQMC_TDM1_GetKFT(tm)
    call DQMC_TDM1_GetErrKFT(tm)
    call DQMC_TDM1_PrintKFT(tm, TDM_UNIT)

    !Compute and print the self-energy
    call DQMC_TDM1_SelfEnergy(tm, tau, TDM_UNIT)

    if(Hub%P2%compute)then
     if(Hub%P2%diagonalize)then
        !Obtain waves from diagonalization
        call DQMC_Phy2_GetIrrep(Hub%P2, Hub%S)
        !Get error for waves
        call DQMC_Phy2_GetErrIrrep(Hub%P2, Hub%P0%G_fun, Hub%S)
        !Analyze symmetry of pairing modes
        call DQMC_Phy2_WaveSymm(Hub%S,Hub%P2,Gwrap%SymmOp)
        !Print Pairing info
        call dqmc_phy2_PrintSymm(Hub%S, Hub%P2, OPT)
     else
        call dqmc_phy2_print(Hub%P2, Hub%S%wlabel, OPT)
     endif
    endif

    ! Clean up the used storage
    call DQMC_TDM1_Free(tm)

    call cpu_time(t2)
    call DQMC_MPI_Final(qmc_sim)
    write(STDOUT,*) "Running time:",  t2-t1, "(second)"

end subroutine run

end module dqmc