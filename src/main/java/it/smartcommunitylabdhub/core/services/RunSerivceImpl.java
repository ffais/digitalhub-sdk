package it.smartcommunitylabdhub.core.services;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import it.smartcommunitylabdhub.core.components.runnables.events.messages.JobMessage;
import it.smartcommunitylabdhub.core.exceptions.CoreException;
import it.smartcommunitylabdhub.core.exceptions.CustomException;
import it.smartcommunitylabdhub.core.models.accessors.utils.TaskAccessor;
import it.smartcommunitylabdhub.core.models.accessors.utils.TaskUtils;
import it.smartcommunitylabdhub.core.models.builders.dtos.RunDTOBuilder;
import it.smartcommunitylabdhub.core.models.builders.entities.RunEntityBuilder;
import it.smartcommunitylabdhub.core.models.builders.kinds.factory.KindBuilderFactory;
import it.smartcommunitylabdhub.core.models.dtos.RunDTO;
import it.smartcommunitylabdhub.core.models.dtos.custom.RunExecDTO;
import it.smartcommunitylabdhub.core.models.entities.Run;
import it.smartcommunitylabdhub.core.repositories.RunRepository;
import it.smartcommunitylabdhub.core.services.interfaces.RunService;
import it.smartcommunitylabdhub.core.services.interfaces.TaskService;

@Service
public class RunSerivceImpl implements RunService {

    @Autowired
    RunDTOBuilder runDTOBuilder;

    private final RunRepository runRepository;
    private final TaskService taskService;
    private final KindBuilderFactory runBuilderFactory;
    private final ApplicationEventPublisher applicationEventPublisher;
    private final RunEntityBuilder runEntityBuilder;

    public RunSerivceImpl(RunRepository runRepository, TaskService taskService, KindBuilderFactory runBuilderFactory,
            ApplicationEventPublisher applicationEventPublisher, RunEntityBuilder runEntityBuilder) {
        this.runRepository = runRepository;
        this.runBuilderFactory = runBuilderFactory;
        this.applicationEventPublisher = applicationEventPublisher;
        this.runEntityBuilder = runEntityBuilder;
        this.taskService = taskService;
    }

    @Override
    public List<RunDTO> getRuns(Pageable pageable) {
        try {
            Page<Run> runPage = this.runRepository.findAll(pageable);
            return runPage.getContent().stream()
                    .map(run -> runDTOBuilder.build(run))
                    .collect(Collectors.toList());

        } catch (CustomException e) {
            throw new CoreException(
                    "InternalServerError",
                    e.getMessage(),
                    HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @Override
    public RunDTO getRun(String uuid) {
        return runRepository.findById(uuid)
                .map(run -> runDTOBuilder.build(run))
                .orElseThrow(() -> new CoreException(
                        "RunNotFound",
                        "The run you are searching for does not exist.",
                        HttpStatus.NOT_FOUND));
    }

    @Override
    public boolean deleteRun(String uuid) {
        try {
            this.runRepository.deleteById(uuid);
            return true;
        } catch (Exception e) {
            throw new CoreException(
                    "InternalServerError",
                    "cannot delete artifact",
                    HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @Override
    public RunDTO save(RunDTO runDTO) {

        return Optional.ofNullable(this.runRepository.save(runEntityBuilder.build(runDTO)))
                .map(run -> runDTOBuilder.build(run))
                .orElseThrow(() -> new CoreException(
                        "RunSaveError",
                        "Problem while saving the run.",
                        HttpStatus.NOT_FOUND));
    }

    @Override
    public RunDTO createRun(RunExecDTO runExecDTO) {

        return Optional.ofNullable(this.taskService.getTask(runExecDTO.getTaskId()))
                .map(taskDTO -> {

                    TaskAccessor taskAccessor = TaskUtils.parseTask(taskDTO.getTask());

                    // build run from task
                    RunDTO runDTO = (RunDTO) runBuilderFactory.getBuilder(taskAccessor.getKind())
                            .build(taskDTO);

                    // Save run
                    Run run = runRepository.save(runEntityBuilder.build(runDTO));

                    // exec run and return run dto

                    return Optional.ofNullable(runDTOBuilder.build(run)).map(
                            r -> {

                                // Override all spec
                                r.getExtra().putAll(runExecDTO.getSpecDTO().getExtra());

                                // produce event with the runDTO object
                                JobMessage jobMessage = new JobMessage(runDTO);
                                applicationEventPublisher.publishEvent(jobMessage);

                                return runDTO;
                            }).orElseThrow(() -> new CoreException("", "", HttpStatus.INTERNAL_SERVER_ERROR));
                }).orElseThrow(() -> new CoreException(
                        "RunNotFound",
                        "The run you are searching for does not exist.",
                        HttpStatus.NOT_FOUND));

    }
}
